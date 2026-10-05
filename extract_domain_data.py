import pandas as pd

# Load only specific named columns
df = pd.read_csv('data/raw/emotion-emotion_69k.csv', usecols = ['emotion', 'empathetic_dialogues', 'labels'])

# Extracts unique values from emotion column if value is a single word string
filtered_mask = df['emotion'].str.match(r'^[a-zA-Z]+$', na=False)
valid_unique_values = df.loc[filtered_mask, 'emotion'].unique()
print(valid_unique_values)

# Removes invalid rows
df = df[df['emotion'].isin(valid_unique_values)]

# Extract dialogue only - remove "Customer :" and "Agent :"
df["dialogue_only"] = df["empathetic_dialogues"].str.extract(
    r"Customer\s*:\s*(.*?)\s*Agent\s*:"
)[0].str.strip()

# Concatanates dialogues and labels into new text column
df['text'] = df['dialogue_only'] + " " + df['labels']

# Creates new csv file with the merged text and emotion labels
df[['text', 'emotion']].to_csv("general_filtered.csv", index=False)