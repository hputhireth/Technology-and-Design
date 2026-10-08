import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
import matplotlib.pyplot as plt
import seaborn as sns

# Loads dataset
df = pd.read_csv('general_final.csv')
df = df.dropna()
# Shuffle rows and reset the index
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df = df.head(3000)

# Load model from HuggingFace
model_name = "BAAI/bge-large-en-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
model.eval() 

def get_normalized_embeddings(texts):
  """Tokenize, extract CLS pooled embeddings, and apply L2 normalization."""
  encoded_input = tokenizer(
      texts, padding=True, truncation=True, return_tensors='pt'
  )
  with torch.no_grad():
    model_output = model(**encoded_input)
    embeddings = model_output[0][:, 0]
  return F.normalize(embeddings, p=2, dim=1)

# Define target anchors
target_prompts = [
    "A positive, pleasant, and uplifting feeling or emotion.",
    "A negative, unpleasant, and distressed feeling or emotion.",
    "A neutral, unbiased, calm, and objective feeling or emotion.",
]
# Encode target sentiments
target_embeddings = get_normalized_embeddings(target_prompts)

# Extracts unique emotion labels and all text from dataset
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
emotion_embeddings = torch.stack(emotion_vectors) 
emotion_embeddings = torch.nn.functional.normalize(
    emotion_embeddings, p=2, dim=1
)

# Compute cosine similarity matrix (num_emotions x 3)
cos_sim_matrix = torch.matmul(emotion_embeddings, target_embeddings.T)

# Softmax probability distribution
temperature = 0.05
probabilities = F.softmax(cos_sim_matrix / temperature, dim=1)

# Creates probability results data frame
df_results = pd.DataFrame({
    "Emotion": emotion_names,
    "Prob_Positive": probabilities[:, 0].numpy(),
    "Prob_Negative": probabilities[:, 1].numpy(),
    "Prob_Neutral": probabilities[:, 2].numpy(),
})

# Set emotion as index and rename columns for cleaner axis labels
heatmap_data = df_results.set_index("Emotion")
heatmap_data.columns = ["Positive", "Negative", "Neutral"]

# Plot heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(
    heatmap_data, 
    annot=True, 
    fmt=".3f", 
    cmap="YlGnBu", 
    vmin=0, 
    vmax=1,
    cbar_kws={'label': 'Probability'}
)

plt.title("Emotion-to-Sentiment Softmax Probability Distribution", fontsize=14, pad=12)
plt.xlabel("Target sentiment", fontsize=11)
plt.ylabel("Emotion category", fontsize=11)
plt.tight_layout()
plt.savefig('softmax.png')
plt.show()
