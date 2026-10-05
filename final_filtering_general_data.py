import pandas as pd

# Loads in CSV file
df = pd.read_csv("general_filtered_balanced.csv")

irrelavant = [
    'sentimental', 'proud', 'jealous', 'grateful', 'embarrassed', 'lonely', 'ashamed', 'guilty', 
    'nostalgic', 'caring', 'disguted'
]

# Removes irrelavant emotions
df = df[~df['emotion'].isin(irrelavant)]

# Creates new CSV file 
df.to_csv("general_final.csv", index=False)