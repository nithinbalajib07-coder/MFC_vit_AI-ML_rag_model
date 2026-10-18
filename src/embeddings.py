"""
Dense Embedding Engine
Uses HuggingFace Transformers (or sentence-transformers) to generate high-quality dense vector embeddings.
"""

import os
import logging
import numpy as np
from typing import List, Union

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingEngine:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = None):
        self.model_name = model_name
        self.device = device
        self._st_model = None
        self._hf_tokenizer = None
        self._hf_model = None
        self._init_model()

    def _init_model(self):
        """Initializes model via sentence-transformers or direct HuggingFace PyTorch pipeline."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer: {self.model_name}")
            self._st_model = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer loaded successfully.")
            return
        except Exception as e:
            logger.info(f"SentenceTransformer not available directly ({e}), using HuggingFace Transformers.")

        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            self.torch = torch
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading HuggingFace AutoModel: {self.model_name} on {self.device}")
            self._hf_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._hf_model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self._hf_model.eval()
            logger.info("HuggingFace AutoModel loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            raise e

    def _mean_pooling(self, model_output, attention_mask):
        """Mean pooling - take attention mask into account for correct averaging."""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = self.torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = self.torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """Encode single text or list of texts into normalized embedding vectors."""
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else texts

        if self._st_model is not None:
            embeddings = self._st_model.encode(text_list, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
            return embeddings[0] if is_single else np.array(embeddings)

        # Direct HuggingFace inference with PyTorch
        all_embeddings = []
        with self.torch.no_grad():
            for i in range(0, len(text_list), batch_size):
                batch = text_list[i:i + batch_size]
                encoded_input = self._hf_tokenizer(batch, padding=True, truncation=True, max_length=256, return_tensors="pt").to(self.device)
                model_output = self._hf_model(**encoded_input)
                sentence_embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])
                # Normalize embeddings
                norm = self.torch.norm(sentence_embeddings, p=2, dim=1, keepdim=True)
                sentence_embeddings = sentence_embeddings / self.torch.clamp(norm, min=1e-9)
                all_embeddings.append(sentence_embeddings.cpu().numpy())

        res = np.vstack(all_embeddings)
        return res[0] if is_single else res
