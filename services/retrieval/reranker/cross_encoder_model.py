# FILE: services/retrieval/reranker/cross_encoder_model.py

import torch
from sentence_transformers import CrossEncoder

class RerankerModel:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RerankerModel, cls).__new__(cls)
            # Use Apple M4 Metal backend if available, else CPU
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            
            # Using Sigmoid activation normalizes the scores to a clean 0.0 - 1.0 probability
            cls._instance.model = CrossEncoder(
                'BAAI/bge-reranker-base', 
                max_length=512, 
                device=device, 
                default_activation_function=torch.nn.Sigmoid()
            )
            print(f"🧠 Cross-Encoder Reranker initialized on {device.upper()}")
        return cls._instance

    def predict(self, pairs):
        return self.model.predict(pairs)