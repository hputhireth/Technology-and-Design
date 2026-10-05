import matplotlib.pyplot as plt
import pandas as pd

# Loads in CSV file
df = pd.read_csv("general_final.csv")

# Loads in emotion data column
emotion_counts = df['emotion'].value_counts()
ax = emotion_counts.plot(kind='bar', color='skyblue', edgecolor='black')

# Bar chart layout formatting and labels
plt.xlabel("Emotions", fontsize=12)
plt.ylabel("Number of occurences", fontsize=12)
plt.title("Emotion distrubution of general dataset", fontsize=14)

# Renders exact count for each bar in graph
ax.bar_label(ax.containers[0], padding=3, fontsize=5)

# For tight layouts
plt.xticks(rotation=45, ha="right") 
plt.tight_layout()

# Displays chart
plt.show()