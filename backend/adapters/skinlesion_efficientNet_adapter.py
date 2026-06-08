import asyncio
import functools
import timm
import torch
from torchvision import transforms
from PIL import Image
import time
import logging
import io
import numpy as np
from typing import Dict, Any, Optional, Tuple
import os

logger = logging.getLogger(__name__)

class EfficientNetAdapter:
    def __init__(self, model_path: str = "./ai_models/skin_lesion_efficientnetb0.pth"):
        self.model_path = model_path
        self.model = None
        self.device = None
        self.transform = None
        self.load_time = None
        
        # Define skin lesion classes
        self.classes = [
            'Actinic keratoses (akiec)',
            'Basal cell carcinoma (bcc)', 
            'Benign keratosis-like lesions (bkl)',
            'Dermatofibroma (df)',
            'Melanoma (mel)',
            'Melanocytic nevi (nv)',
            'Vascular lesions (vasc)'
        ]
        
        self.class_labels = {
            0: 'Actinic keratoses (akiec)',
            1: 'Basal cell carcinoma (bcc)', 
            2: 'Benign keratosis-like lesions (bkl)',
            3: 'Dermatofibroma (df)',
            4: 'Melanoma (mel)',
            5: 'Melanocytic nevi (nv)',
            6: 'Vascular lesions (vasc)'
        }
    
    async def load_model(self):
        """Load the model asynchronously"""
        try:
            logger.info(f"🖼️ Loading skin lesion model from {self.model_path}")
            start_time = time.time()
            
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load real model
            self.model = timm.create_model('efficientnet_b0', num_classes=len(self.classes))
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
        
            self.model.to(self.device)
            self.model.eval()
            
            # Set up transforms
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.7630331, 0.5456457, 0.5700467],  
                    std=[0.1409281, 0.15261227, 0.16997086]     
                )
            ])
            
            self.load_time = time.time() - start_time
            
            logger.info(f"✅ Skin lesion model loaded in {self.load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load skin lesion model: {e}")
            raise

    def _validate_image(self, image: Image.Image) -> Image.Image:
        """Validate and convert image format"""
        try:
            image.load()  # Verify that it is an image
            
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' or 'transparency' in image.info):
                image = image.convert('RGB')
                
            return image
            
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

    def _calculate_confidence_scores(self, prediction: torch.Tensor) -> Dict[str, float]:
        """Calculate confidence scores for all classes"""
        confidence_scores = torch.nn.functional.softmax(prediction, dim=1)[0] * 100
        return {self.class_labels[i]: float(score) for i, score in enumerate(confidence_scores)}

    def _predict_sync(self, image: Image.Image) -> Tuple[str, Dict[str, float]]:
        """Synchronous prediction - returns class label and confidence scores"""
        # Validate image
        validated_image = self._validate_image(image)
        
        # Transform and predict
        input_tensor = self.transform(validated_image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            prediction = self.model(input_tensor)
            
            # Get predicted class
            _, predicted_class = torch.max(prediction, 1)
            predicted_index = predicted_class.item()
            predicted_class_label = self.class_labels.get(predicted_index, "Unknown")
            
            # Get confidence scores
            confidence_scores = self._calculate_confidence_scores(prediction)
            
        return predicted_class_label, confidence_scores
    
    async def classify_image(self, image: Image.Image) -> torch.Tensor:
        """Async wrapper for classification - returns tensor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(self._predict_sync, image))
    
    async def cleanup(self):
        """Cleanup model resources"""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            self.is_loaded = False
            logger.info("✅ Skin lesion adapter cleaned up")
        except Exception as e:
            logger.error(f"❌ Skin lesion cleanup failed: {e}")