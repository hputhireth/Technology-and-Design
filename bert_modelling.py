import pandas as pd
import numpy as np

# 1. Load and Prepare the Data
df = pd.read_csv('general_final.csv')

# Drop missing values to prevent training errors
df = df.dropna(subset=['text', 'emotion'])
df = df.head(100)

# Encode string 'emotion' labels into integer 'label' column required by Hugging Face
emotion_to_sentiment = {
    'afraid' : 0, 
    'angry': 0, 
    'annoyed': 0, 
    'anticipating': 0, 
    'anxious': 0,
    'apprehensive': 0,
    'confident': 1,
    'content': 1,
    'devastated': 0,
    'disappointed': 0,
    'excited': 1, 
    'faithful': 1,
    'furious': 1,
    'hopeful': 1,
    'impressed': 1,
    'joyful': 1,
    'prepared': 1,
    'sad': 0,
    'surprised': 1,
    'trusting': 1
}
df['sentiment'] = df['emotion'].map(emotion_to_sentiment)

