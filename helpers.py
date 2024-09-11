from collections import defaultdict

def rank_llms(llms):
    metrics = defaultdict(list)
    
    for llm in llms:
        metrics[llm.llm_name].append(llm.value)
    
    # Calculate mean of values for each LLM
    avg_metrics = {llm: sum(values)/len(values) for llm, values in metrics.items()}
    
    # Rank by mean values
    ranked_llms = sorted(avg_metrics.items(), key=lambda x: x[1])
    
    return ranked_llms
