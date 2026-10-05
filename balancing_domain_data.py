import pandas as pd

# Loads in CSV file
df = pd.read_csv("general_filtered.csv")

# Shuffles data frame randomly
df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Create the new datafame based on the first 2000 rows of any unique 'emotion' in shuffled data frame
balance_df = df_shuffled.groupby('emotion').head(2000).copy()

# Creates new CSV file
balance_df[['text', 'emotion']].to_csv("general_filtered_balanced.csv", index=False)