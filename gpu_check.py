import torch
print(torch.backends.mps.is_available())  # Should be True on M1
print(torch.backends.mps.is_built())

# In embeddings.py or wherever you load the model
from sentence_transformers import SentenceTransformer
import torch

device = 'mps' if torch.backends.mps.is_available() else 'cpu'
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

print(f"Embedding model on: {device}")  # Should say "mps"