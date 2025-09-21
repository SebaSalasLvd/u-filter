from transformers import pipeline

# Load Spanish BERT pretrained model for text classification
bert_pipeline = pipeline(
    "text-classification",
    model="dccuchile/bert-base-spanish-wwm-cased",
    tokenizer="dccuchile/bert-base-spanish-wwm-cased"
)

bert_pipeline_test = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment"
    )
