from transformers import pipeline

# BERT entrenado en español de chile este es el que deberiamos usar pero necesita fine-tuning
bert_pipeline = pipeline(
    "text-classification",
    model="dccuchile/bert-base-spanish-wwm-cased",
    tokenizer="dccuchile/bert-base-spanish-wwm-cased"
)

#BERT pre-entrenado para multiples lenguajes este es de base para que responda algo por mientras
bert_pipeline_test = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
