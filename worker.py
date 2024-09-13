import json
import os
import pika
from sqlalchemy.orm import Session
from database import get_db
from tenacity import retry, wait_fixed, stop_after_attempt

from main import simulate_data, get_ranked_llms

# RabbitMQ connection parameters
rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
rabbitmq_queue = "tasks"

# Task mappings (task names to functions)
task_mapping = {
    "simulate_data": lambda db, params: simulate_data(db),  
    "rank_llms": lambda db, params: get_ranked_llms(db,params) 
}

@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))
def execute_task(task_name: str, db: Session, params: dict):
    """Execute a task from the task mapping."""
    if task_name in task_mapping:
        task_mapping[task_name](db, params)
    else:
        raise ValueError(f"Unknown task: {task_name}")


def process_task(ch, method, properties, body):
    """Process a generic task from the RabbitMQ queue."""
    db = get_db()
    message = body.decode('utf-8')
    task_data = json.loads(message)
    task_name = task_data['task']
    params = task_data.get('params', {})
    message = body.decode('utf-8')

    try:
        execute_task(task_name, db, params)
        print(f"Task {task_name} processed successfully")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing task {task_name}: {e}")


def consume_queue():
    """Consume tasks from RabbitMQ."""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue, durable=True)

    channel.basic_qos(prefetch_count=1)  # Fair dispatch
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=process_task)

    print("Waiting for tasks. To exit, press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    consume_queue()
