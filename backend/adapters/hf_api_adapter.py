from huggingface_hub import InferenceClient
from .base import ModelInterface
from typing import Any, Dict, List, Union
import io
from PIL import Image
import asyncio

STREAM = False # Global setting for non-streaming

class HuggingFaceAdapter(ModelInterface):  
    def __init__(self, 
                 multipurpose_model: str,
                 api_key: str,
                ):
        self.clients = {
            "multipurpose": InferenceClient(model=multipurpose_model, token=api_key), 
        }
        
    # _get_text_generation_response method removed

    #1- Multipurpose LLM functions
    async def chat(self, prompt: str, context: Union[str, None] = None) -> str:
        if context: 
            prompt = f"{context}\n{prompt}"
        
        raw_response = self.clients["multipurpose"].text_generation(
            prompt,
            max_new_tokens=15, 
            temperature=0.7,
            stream=False 
        )
        if isinstance(raw_response, str):
            return raw_response
        elif asyncio.iscoroutine(raw_response):
            return await raw_response
        else:
            return str(raw_response)
        
    async def plan_and_call_tools(self, user_input: str, available_tools: List[str]) -> Dict[str, Any]:
        prompt = f"Given this user input: '{user_input}', determine and sequence the tools required to respond based on the available tools: {available_tools}. Provide a detailed plan of action."

        raw_response = self.clients["multipurpose"].text_generation(
            prompt,
            max_new_tokens=15,
            # temperature is not specified, can be added if needed, defaults to client's/model's default
            stream=False
        )
        
        response_text: str
        if isinstance(raw_response, str):
            response_text = raw_response
        elif asyncio.iscoroutine(raw_response):
            response_text = await raw_response
        else:
            response_text = str(raw_response)
            
        return {"tool_plan": response_text}
    
    async def summary_to_report(self, dialogue: str, diagnosis: str) -> str:
        prompt = f"Generate a medical report based on the following dialogue: '{dialogue}' and diagnosis: '{diagnosis}'."
        
        raw_response = self.clients["multipurpose"].text_generation(
            prompt,
            max_new_tokens=15,
            temperature=0.7,
            stream=False
        )
        if isinstance(raw_response, str):
            return raw_response
        elif asyncio.iscoroutine(raw_response):
            return await raw_response
        else:
            return str(raw_response)
    
    #2- textDiagnosis Model Functions
    async def generate_diagnosis(self, symptoms: str, context: Union[str, None] = None) -> str:
        if context: 
            symptoms = f"{context}\n{symptoms}"
            
        raw_response = self.clients["multipurpose"].text_generation(
            symptoms,
            max_new_tokens=15, 
            temperature=0.7,
            stream=False
        )
        if isinstance(raw_response, str):
            return raw_response
        elif asyncio.iscoroutine(raw_response):
            return await raw_response
        else:
            return str(raw_response)