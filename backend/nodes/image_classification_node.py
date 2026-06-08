import asyncio
import io
import torch
from PIL import Image
from adapters.skinlesion_efficientNet_adapter import EfficientNetAdapter
from typing import Any
from managers.model_manager import model_manager
import base64
    
class ImageClassificationNode:
    def __init__(self, adapter: EfficientNetAdapter):
        self.adapter = adapter

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        """Classify uploaded medical image"""
        print("📸 IMAGE CLASSIFICATION NODE CALLED!")

        state["current_workflow_stage"] = "analyzing_image"
        
        # Process the image
        state = await self.classify_skinLesion(state)
        
        state["current_workflow_stage"] = "image_analysis_complete"
        print("✅ Image classification complete")
        return state
        
    async def classify_skinLesion(self, state: dict[str, Any]) -> dict[str, Any]:
        image_input = state.get("image_input")
        
        if not image_input:             # No image provided
            state["skin_lesion_analysis"] = {
                "image_diagnosis": "No image provided",
                "confidence_score": {}
            }
            return state
        
        try:
            # Handle both base64 string and bytes
            if isinstance(image_input, str):
                # Convert base64 to bytes
                image_bytes = base64.b64decode(image_input)
            elif isinstance(image_input, bytes):
                image_bytes = image_input
            else:
                raise ValueError("Image input must be base64 string or bytes")
                
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes)) 
            
            # Let the adapter handle all the classification logic
            predicted_class_label, confidence_scores = await self.adapter.classify_image(pil_image)
            
            # Update state with results
            state["skin_lesion_analysis"] = {
                "image_diagnosis": predicted_class_label,
                "confidence_score": confidence_scores
            }
            
        except Exception as e:
            state["skin_lesion_analysis"] = {
                "image_diagnosis": f"Error analyzing image: {str(e)}",
                "confidence_score": {}
            }
            state["current_workflow_stage"] = "image_analysis_error"
        
        return state
    
    #direct classification method for non-LangGraph usage
    async def classify_image_direct(self, skinLesion_imageFile: bytes) -> tuple[str, dict[str, float]]:
        """Direct classification method for non-LangGraph usage"""
        try:
            image = Image.open(io.BytesIO(skinLesion_imageFile))
            return await self.adapter.classify_image(image)
            
        except Exception as e:
            return f"Error: {str(e)}", {}