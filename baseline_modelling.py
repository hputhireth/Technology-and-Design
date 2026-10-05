import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Load dataset
df = pd.read_csv('general_final.csv')
df = df.dropna()

# Define features (X) and target (y)
X = df['text']
y = df['emotion']

# Split data into training and testing sets (80/20 split)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Convert text to numerical feature vectors using TF-IDF
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Initialize logistic regression model for training
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# Create model
with open("general_baseline_model.pkl", "wb") as f:
    pickle.dump(model, f)