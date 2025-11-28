import os
import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType

# Configuration
TRAIN_FILE = "../../data/aid_training_data.jsonl"
OUTPUT_DIR = "../../models/aid_distiller"
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"

def train():
    print("⏳ Loading AID Dataset...")
    df = pd.read_json(TRAIN_FILE, lines=True)
    dataset = Dataset.from_pandas(df)
    dataset = dataset.train_test_split(test_size=0.1)
    
    print("⏳ Loading Model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        r=16, # Increased rank for unified task
        lora_alpha=32,
        lora_dropout=0.1
    )
    model = get_peft_model(model, peft_config)
    
    def preprocess_function(examples):
        # Unified Prompt
        inputs = [f"Instruction: Distill this interface for query: \"{q}\"\nFull Schema: {s}\n\nDistilled Interface: " 
                  for q, s in zip(examples["query"], examples["full_schema"])]
        targets = [t + tokenizer.eos_token for t in examples["target_output"]]
        
        model_inputs = tokenizer(inputs, max_length=2048, truncation=True, padding="max_length")
        labels = tokenizer(targets, max_length=2048, truncation=True, padding="max_length")
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_datasets = dataset.map(preprocess_function, batched=True)
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        num_train_epochs=1,
        fp16=True,
        save_steps=50,
        logging_steps=10,
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model)
    )
    
    print("🚀 Starting AID Training...")
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    train()
