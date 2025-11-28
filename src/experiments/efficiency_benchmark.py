import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer
import sys
sys.path.append("../aid_framework")
from inference import InterfaceDistiller

# Configuration
TEST_DATA = "../../data/aid_training_data.jsonl" # Use subset for test
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"

def count_tokens(tokenizer, text):
    return len(tokenizer.encode(text))

def run_benchmark():
    print("🚀 Running Efficiency Benchmark...")
    
    # Load Data
    df = pd.read_json(TEST_DATA, lines=True).head(50) # Test on 50 examples
    
    # Load Model
    distiller = InterfaceDistiller()
    tokenizer = distiller.tokenizer
    
    results = []
    
    for _, row in df.iterrows():
        query = row['query']
        full_schema = json.loads(row['full_schema'])
        
        # 1. Distill
        mini_schema, _ = distiller.distill(query, full_schema)
        
        # 2. Measure
        full_tokens = count_tokens(tokenizer, json.dumps(full_schema))
        mini_tokens = count_tokens(tokenizer, json.dumps(mini_schema))
        
        reduction = (1 - (mini_tokens / full_tokens)) * 100
        
        results.append({
            "Query": query[:30] + "...",
            "Full Tokens": full_tokens,
            "Distilled Tokens": mini_tokens,
            "Reduction (%)": reduction
        })
        print(f"Query: {query[:20]}... | {full_tokens} -> {mini_tokens} ({reduction:.1f}%)")
        
    # Plot
    res_df = pd.DataFrame(results)
    print(f"Average Reduction: {res_df['Reduction (%)'].mean():.1f}%")
    
    plt.figure(figsize=(10, 6))
    sns.histplot(res_df['Reduction (%)'], bins=20, kde=True)
    plt.title("Token Reduction Distribution")
    plt.xlabel("Reduction (%)")
    plt.savefig("efficiency_plot.png")
    print("✅ Saved efficiency_plot.png")

if __name__ == "__main__":
    run_benchmark()
