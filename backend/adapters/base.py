from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
import time
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelInterface(ABC):
    """Abstract base class for all model adapters."""
    
    ##Web Functionalities 
    @abstractmethod
    async def load_model(self) -> None:
        """Load the model into memory. This is called once at startup."""
        pass

    
    
    @abstractmethod
    async def generate_diagnosis(self, symptoms: str, context: Union[str, None] = None) -> str:
        """LLM-based diagnosis generation- Text Symptom Diagnosis via domain-specific 
        reasoning and outputs preliminary diagnoses, requiring specialized prompt structures 
        distinct from general LLM use"""
        pass
    
    # @abstractmethod
    # async def generate_followup_questions(self, diagnosis, reasoning, confidence) -> str:
    #     """Generates follow-up questions based on the diagnosis, reasoning, and confidence level.
    #     This is used to refine the diagnosis or gather more information."""
    #     pass
    
    @abstractmethod
    async def generate_overall_instance1(self, symptoms: str, diagnosis: str, confidence: float) -> str:
        """Generate enhanced analysis for textual-only workflow (Instance 1)"""
        pass

    @abstractmethod
    async def generate_overall_instance2(self, skin_symptoms: str, image_diagnosis: str, image_confidence: Dict) -> str:
        """Generate analysis for textual + image workflow (Instance 2)"""
        pass

    @abstractmethod
    async def generate_overall_instance3(self, original_symptoms: str, followup_responses: Dict, enhanced_diagnosis: str, enhanced_confidence: float) -> str:
        """Generate analysis for textual + follow-up workflow (Instance 3)"""
        pass

    # @abstractmethod
    # async def generate_overall_instance4(self, original_symptoms: str, followup_responses: Dict, followup_diagnosis: Dict, skin_symptoms: str, image_analysis: Dict) -> str:
    #     """Generate comprehensive analysis for all data workflow (Instance 4)"""
    #     pass
    
    @abstractmethod
    async def generate_medical_report(self, report_prompt: str) -> str:
        """Generates a medical report based on the provided report prompt.
        This is used to compile all relevant information into a structured report."""
        pass