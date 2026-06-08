"""Embedding model adapter for medical text processing"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
import os

logger = logging.getLogger(__name__)

class EmbedderAdapter:
    """Embedding model adapter for medical text similarity and search"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedder = None
        self.is_loaded = False
        self.load_time = None
        self.embedding_dim = None
        
    async def load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"🔍 Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            try:
                from sentence_transformers import SentenceTransformer
                
                # Try to load the model
                self.embedder = SentenceTransformer(self.model_name)
                
                # Test the model to get embedding dimension
                test_embedding = self.embedder.encode("test text")
                self.embedding_dim = len(test_embedding)
                
                logger.info(f"✅ Real embedding model loaded ({self.embedding_dim}D)")
                
            except ImportError:
                logger.warning("⚠️ sentence-transformers not installed, using mock embedder")
                self.embedder = "mock_embedder"
                self.embedding_dim = 384  # Common embedding dimension
            except Exception as e:
                logger.warning(f"⚠️ Failed to load real embedder: {e}, using mock")
                self.embedder = "mock_embedder" 
                self.embedding_dim = 384
            
            self.load_time = time.time() - start_time
            self.is_loaded = True
            
            logger.info(f"✅ Embedding adapter ready in {self.load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.is_loaded = False
            raise
    
    async def encode_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Encode text into embeddings"""
        if not self.is_loaded:
            raise Exception("Embedding model not loaded")
        
        try:
            start_time = time.time()
            
            # Handle mock embedder
            if self.embedder == "mock_embedder":
                embeddings = self._generate_mock_embeddings(text)
            else:
                # Real embedding generation
                embeddings = self.embedder.encode(text)
            
            inference_time = time.time() - start_time
            
            # Ensure numpy array format
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)
            
            logger.debug(f"🔍 Encoded text in {inference_time:.3f}s")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Text encoding failed: {e}")
            raise
    
    async def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        try:
            # Get embeddings
            embedding1 = await self.encode_text(text1)
            embedding2 = await self.encode_text(text2)
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(embedding1, embedding2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Similarity computation failed: {e}")
            return 0.0
    
    async def find_most_similar(self, query_text: str, candidate_texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar texts from a list of candidates"""
        try:
            if not candidate_texts:
                return []
            
            # Encode query
            query_embedding = await self.encode_text(query_text)
            
            # Encode all candidates
            candidate_embeddings = await self.encode_text(candidate_texts)
            
            # Compute similarities
            similarities = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = self._cosine_similarity(query_embedding, candidate_embedding)
                similarities.append({
                    "text": candidate_texts[i],
                    "similarity": float(similarity),
                    "index": i
                })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Similar text search failed: {e}")
            return []
    
    async def cluster_symptoms(self, symptoms_list: List[str], num_clusters: int = 3) -> Dict[str, Any]:
        """Cluster similar symptoms together"""
        try:
            if len(symptoms_list) < num_clusters:
                return {"clusters": [symptoms_list], "cluster_labels": [0] * len(symptoms_list)}
            
            # Get embeddings
            embeddings = await self.encode_text(symptoms_list)
            
            # Simple clustering (using mock for now)
            if self.embedder == "mock_embedder":
                cluster_labels = self._mock_clustering(symptoms_list, num_clusters)
            else:
                # You could implement real clustering here with sklearn
                cluster_labels = self._simple_clustering(embeddings, num_clusters)
            
            # Organize results
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(symptoms_list[i])
            
            return {
                "clusters": list(clusters.values()),
                "cluster_labels": cluster_labels,
                "num_clusters": len(clusters)
            }
            
        except Exception as e:
            logger.error(f"❌ Symptom clustering failed: {e}")
            return {"clusters": [symptoms_list], "cluster_labels": [0] * len(symptoms_list)}
    
    def _generate_mock_embeddings(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate mock embeddings for testing"""
        import hashlib
        
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        embeddings = []
        for t in texts:
            # Create deterministic "embedding" based on text hash
            hash_obj = hashlib.md5(t.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to pseudo-embedding
            embedding = np.array([b / 255.0 for b in hash_bytes])
            
            # Pad or truncate to desired dimension
            if len(embedding) < self.embedding_dim:
                padding = np.random.random(self.embedding_dim - len(embedding)) * 0.1
                embedding = np.concatenate([embedding, padding])
            else:
                embedding = embedding[:self.embedding_dim]
            
            embeddings.append(embedding)
        
        result = np.array(embeddings)
        
        # Return single array if input was single string
        if isinstance(text, str):
            return result[0]
        
        return result
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        try:
            # Handle different array shapes
            if vec1.ndim > 1:
                vec1 = vec1.flatten()
            if vec2.ndim > 1:
                vec2 = vec2.flatten()
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"❌ Cosine similarity computation failed: {e}")
            return 0.0
    
    def _mock_clustering(self, symptoms_list: List[str], num_clusters: int) -> List[int]:
        """Mock clustering based on text length"""
        # Simple mock: cluster by text length
        lengths = [len(text) for text in symptoms_list]
        min_len, max_len = min(lengths), max(lengths)
        
        if max_len == min_len:
            return [0] * len(symptoms_list)
        
        cluster_labels = []
        for length in lengths:
            # Assign cluster based on relative length
            normalized_length = (length - min_len) / (max_len - min_len)
            cluster = int(normalized_length * (num_clusters - 1))
            cluster_labels.append(min(cluster, num_clusters - 1))
        
        return cluster_labels
    
    def _simple_clustering(self, embeddings: np.ndarray, num_clusters: int) -> List[int]:
        """Simple clustering using k-means"""
        try:
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            return cluster_labels.tolist()
            
        except ImportError:
            logger.warning("⚠️ scikit-learn not available, using mock clustering")
            return self._mock_clustering([f"text_{i}" for i in range(len(embeddings))], num_clusters)
        except Exception as e:
            logger.error(f"❌ K-means clustering failed: {e}")
            return [0] * len(embeddings)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "loaded": self.is_loaded,
            "model_name": self.model_name,
            "load_time": self.load_time,
            "embedding_dimension": self.embedding_dim,
            "is_mock": self.embedder == "mock_embedder"
        }
    
    async def cleanup(self):
        """Cleanup embedding model resources"""
        try:
            if self.embedder and self.embedder != "mock_embedder":
                del self.embedder
            self.embedder = None
            self.is_loaded = False
            logger.info("✅ Embedding adapter cleaned up")
        except Exception as e:
            logger.error(f"❌ Embedding cleanup failed: {e}")