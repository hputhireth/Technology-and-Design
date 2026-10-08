import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import seaborn as sns
import matplotlib.pyplot as plt

# Load the dataset
df = pd.read_csv('general_final.csv')
df = df.dropna()

# Load the tokenizer and models
model_name = "BAAI/bge-large-en-v1.5" # https://huggingface.co/BAAI/bge-large-en-v1.5
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Set model to evaluation mode (essential before extracting embeddings or inference)
model.eval()

# Extract labels as keys and values
emotion_names = df['emotion'].unique().tolist()
sentences = df['text'].tolist()

def encode_texts(texts, batch_size=32):
  all_embeddings = []
  for i in range(0, len(texts), batch_size):
    batch = texts[i : i + batch_size]
    encoded_input = tokenizer(
        batch, padding=True, truncation=True, return_tensors='pt'
    )
    with torch.no_grad():
      model_output = model(**encoded_input)
      embeddings = model_output[0][:, 0]
      all_embeddings.append(embeddings)
  return torch.cat(all_embeddings, dim=0)

# Get sentence embeddings for all text rows in the dataset
sentence_embeddings = encode_texts(sentences)

emotion_vectors = []
for emotion in emotion_names:
  # Filter sentence embeddings belonging to the current emotion label
  mask = (df['emotion'] == emotion).values
  emotion_sentence_embeds = sentence_embeddings[mask]

  # Calculate mean
  mean_vec = emotion_sentence_embeds.mean(dim=0)
  emotion_vectors.append(mean_vec)
  
# Stack and L2-normalize emotion label vectors
emotion_embeddings = torch.stack(
    emotion_vectors
) 
emotion_embeddings = torch.nn.functional.normalize(
    emotion_embeddings, p=2, dim=1
)

# Calculate cosine similarity for each emotion label
num_emotions = len(emotion_names)
cos_sim_matrix = torch.matmul(emotion_embeddings, emotion_embeddings.T)

# --- Generate heatmap for Cosine Similarity ---

# Slice matrix to match emotion_names count if sentence embeddings count differs
cos_sim_submatrix = cos_sim_matrix[:num_emotions, :num_emotions].numpy()


# Create data frame and export to CSV
cos_sim_df = pd.DataFrame(cos_sim_submatrix, index=emotion_names, columns=emotion_names)
cos_sim_df.to_csv("cosine_similarity_matrix.csv")

# Generate and save Heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(cos_sim_df, annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
plt.title("Cosine Similarity Heatmap")
plt.xlabel("Emotions")
plt.ylabel("Emotions")
plt.tight_layout()
plt.savefig("cosine_similarity_heatmap.png")
plt.show()
