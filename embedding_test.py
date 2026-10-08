import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel

# Load the dataset
df = pd.read_csv('general_final.csv')
df = df.dropna()
df = df.head(100)

# Load the tokenizer and models
model_name = "BAAI/bge-large-en-v1.5" # https://huggingface.co/BAAI/bge-large-en-v1.5
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Set model to evaluation mode (essential before extracting embeddings or inference)
model.eval()

# Extract labels as keys and values
emotion_names = df['emotion'].unique().tolist()
sentences = df['text'].tolist()

# Tokenize the input sentences
encoded_input = tokenizer(
    sentences, 
    padding=True, truncation=True, # Padding and truncation ensure all sequences in the batch have the same length
    return_tensors='pt' # Return PyTorch tensors
)

# Perform the normal forward pass
with torch.no_grad():
    model_output = model(**encoded_input)
    # Perform CLS pooling.
    sentence_embeddings = model_output[0][:, 0]

# Normalize the embeddings using L2-norm
sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)

# Calculate cosine similarity and euclidean distance for each label
num_emotions = len(emotion_names)

print("--- Cosine similarity ---")
cos_sim_matrix = torch.matmul(sentence_embeddings, sentence_embeddings.T)

for i in range(num_emotions):
    for j in range(i + 1, num_emotions):
        sim = cos_sim_matrix[i, j].item()
        print(f"{emotion_names[i]} vs {emotion_names[j]} : {sim:.4f}")

print("\n--- Euclidean distance ---")
euc_dist_matrix = torch.cdist(sentence_embeddings, sentence_embeddings, p=2)

for i in range(num_emotions):
    for j in range(i + 1, num_emotions):
        dist = euc_dist_matrix[i, j].item()
        print(f"{emotion_names[i]} vs {emotion_names[j]} : {dist:.4f}")