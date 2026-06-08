from ..base import ModelInterface
from typing import Any, Dict, List, Union
import asyncio
import functools
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import logging
import time

logger = logging.getLogger(__name__)

class LocalModelAdapter(ModelInterface):  
    def __init__(self, 
                 llm_path: str): #locks the model in RAM, which can improve inference speed by preventing paging.
        self.model_path = llm_path
        self.model = None
        self.load_time = None
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
    # Older version of the system prompt for reference
    # """You a helpful, expert AI-powered medical assistant specialized in text symptom evaluation and general health guidance. 
            
    # Follow these instructions at all times:

    # 1. **IDENTITY & PURPOSE**
    # - You are not a licensed medical professional, but you provide evidence-based medical information.
    # - Your role is to interpret user-described symptoms (text and/or images), give potential explanations, advise on urgency of care, and offer general health education.
    # - Always include a clear disclaimer: "I am not a licensed healthcare provider. My responses are informational only and not a substitute for professional medical advice."

    # 2. **SCOPE & LIMITATIONS**
    # - Address only health/medical questions. If the user asks about non-medical topics, respond politely that you can only help with medical matters.
    # - If uncertain, say "I'm not sure; please consult a qualified healthcare professional."

    # 3. **EVIDENCE-BASED & PREVENT HALLUCINATIONS**
    # - Only share well-established medical facts or widely accepted clinical guidelines.
    # - Do not fabricate sources or make up treatment protocols.
    # - When using medical terms, define them briefly in plain language.

    # 4. **SAFETY & TRIAGE**
    # - Recognize "red-flag" symptoms (e.g., chest pain, difficulty breathing, uncontrolled bleeding, stroke signs).
    # - If identified, instruct the user to seek immediate medical attention (e.g., "Call emergency services or go to the nearest hospital.").
    # - For mild to moderate symptoms, suggest general, conservative self-care (e.g., rest, hydration, over-the-counter meds) but remind users to follow up with a provider if symptoms persist.

    # 5. **PRIVACY & CONFIDENTIALITY**
    # - Do not ask for or store personally identifiable information (e.g., full name, address).
    # - Remind users to protect their own privacy when describing sensitive details.

    # 6. **TONE & STYLE**
    # - Be empathetic, respectful, and patient.
    # - Use clear, concise sentences.
    # - Include bullet points or numbered steps for clarity when listing differential diagnoses or management advice.

    # 7. **CLOSING RECOMMENDATION**
    # - End each interaction with a reminder to seek professional care if unsure or if symptoms worsen.
    # - Example closing: "If your condition does not improve or you have any concerns, please consult your healthcare provider promptly."
    # """
        return (
            "You are a helpful, expert AI-powered medical assistant specialized in text symptom evaluation and general health guidance.\n"
            "Always include this disclaimer: 'I am not a licensed healthcare provider. My responses are informational only and not a substitute for professional medical advice.'\n\n"
            "Follow these rules:\n"
            "- Only discuss health/medical topics.\n"
            "- If unsure, say so and recommend seeing a healthcare provider.\n"
            "- Do not hallucinate or fabricate facts.\n"
            "- Define medical terms simply.\n"
            "- Identify red-flag symptoms and escalate when necessary.\n"
            "- Be concise, empathetic, and structured.\n"
            "- stop generating if <|end_of_text|> is reached.\n"
        )
        
    async def load_model(self):
        """Load the medical LLM model"""
        try:
            logger.info(f"🧠 Loading LLM from {self.model_path}")
            start_time = time.time()
            
            # Initialize llama-cpp model
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=8192,           # Context window
                n_threads=8,          # CPU threads
                n_gpu_layers=-1,  # GPU layers
                verbose=True,            # Enable verbose for debugging
                f16_kv=True,
                use_mlock=True,
                temperature=0.7,         # Add temperature
                top_p=0.9,              # Add top_p
            )
            
            self.load_time = time.time() - start_time
            logger.info(f"✅ LLM loaded successfully in {self.load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load LLM: {e}")
            raise

    async def run_sync(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        func_with_kwargs = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_with_kwargs)

    def _format_prompt(self, user_input: str) -> str:
        return (
            # "<|begin_of_text|>"
            "<|start_header_id|>system<|end_header_id|>\n"
            f"{self.system_prompt}<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n"
            f"{user_input}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n"
        )

    def _generate_text_sync(self, prompt: str, max_tokens: int = 512, temperature: float = 0.3) -> str:
        try:
            if not self.model:
                raise ValueError("Model not loaded")
            
            # Format using Llama-3 chat template
            formatted_prompt = self._format_prompt(prompt)
            
            # Use direct generation instead of chat completion
            response = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["<|eot_id|>", "<|end_of_text|>", "STOP"],
                echo=False
            )
            result = response['choices'][0]['text'].strip()
            logger.debug(f"🧠 Generated output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return ""

    async def generate_diagnosis(self, symptoms: str, context: Union[str, None] = None) -> str: 
        DIAGNOSIS_PROMPT_TEMPLATE = """
Diagnose based on the following symptoms: {symptoms}
## INSTRUCTIONS:
STRICTLY follow the format below with NO markdown or extra symbols.
Do NOT use numbering, bold, or extra notes. Match keys EXACTLY.

## Step 1: Skin Cancer Screening
Carefully check if these symptoms may indicate **any** of the following skin-related conditions such as Melanocytic Nevi, Melanoma, Benign keratosis-like lesions, Basal Cell Carcinoma, Actinic Keratoses, Vascular Lesions, Dermatofibroma or any skin growth, mole, lesion, bump, spot, skin changes

Determine if further analysis requiring a skin lesion image is needed based on the symptoms provided. 

- ImageRequired: <Yes/No>

## Step 2: General Diagnosis 
Generate up to 5 most possible diagnoses using the format below:

- Diagnosis: <condition name>
- Reasoning: <justification>
- Confidence: <value between 0 and 1>
- Severity: <mild | moderate | severe | critical | emergency>

Repeat the above 4 lines per diagnosis. No additional text allowed.
"""

        prompt = DIAGNOSIS_PROMPT_TEMPLATE.format(symptoms=symptoms)
        return await self.run_sync(self._generate_text_sync, prompt, 512, 0.5)

    async def generate_followup_questions(self, diagnosis, reasoning, confidence):
        prompt = (
            f"Initial diagnosis: {diagnosis} ({confidence:.2f})\n"
            f"Reasoning: {reasoning}\n\n"
            "Generate 3-5 follow-up questions to clarify the condition:\n"
            "- Symptom details/duration\n"
            "- Related symptoms\n"
            "- Medical history\n"
            "- Lifestyle risks"
        )
        return await self.run_sync(self._generate_text_sync, prompt, 512, 0.5)
    
    async def generate_self_care_advice(self, prompt: str) -> str:
        """Generate self-care advice for specific conditions"""
        full_prompt = (
        "You are a healthcare advisor providing self-care recommendations.\n" 
        
        f"{prompt}\n"
        
        "Provide practical, safe, and evidence-based self-care advice.\n"
        "Focus on immediate relief measures and when to seek professional care.\n"
        "Format as clear, actionable bullet points.\n"
        )
        return await self.run_sync(self._generate_text_sync, full_prompt, 512, 0.4)
    
    async def retrieve_medical_evidence(self, diagnosis: str) -> List[str]:
        """Retrieve supporting medical evidence for a diagnosis (RAG-style)"""
        prompt = f"""
        Provide 2-3 evidence-based facts or guidelines related to: {diagnosis}
        
        Focus on:
        1. Clinical presentation
        2. Standard treatment approaches  
        3. When to seek specialist care
        
        Format each as a separate, concise statement.
        Reference medical guidelines where applicable.
        """
        
        result = await self.run_sync(self._generate_text_sync, prompt, 300, 0.3)
        return [line.lstrip('-•*0123456789. ').strip() for line in result.split('\n') if line.strip()][:3]
    
    async def generate_medical_evidence(self, prompt: str) -> str:
        """Generate evidence-based medical recommendations"""
        full_prompt = (
        "You are a medical evidence specialist. Provide evidence-based recommendations with the input below:\n"
        
        f"{prompt}\n"
        
        "Reference established medical guidelines and clinical best practices.\n"
        "Keep recommendations concise and clinically relevant.\n"
        "Mention the strength of evidence when possible."
        )
        return await self.run_sync(self._generate_text_sync, full_prompt, 400, 0.3)

    #Currently not included within overall_analysis_node 
    async def analyze_combined_data(self, textual_analysis: Dict, image_analysis: Dict = None) -> str:
        """Analyze combined textual and image data for comprehensive diagnosis"""
        
        prompt = (
            "TEXTUAL ANALYSIS:\n"
            f"- Diagnosis: {textual_analysis.get('text_diagnosis', 'Unknown')}\n"
            f"- Confidence: {textual_analysis.get('diagnosis_confidence', 0)}\n"
            f"- Severity: {textual_analysis.get('severity', 'Unknown')}\n"
            f"- Reasoning: {textual_analysis.get('reasoning', 'None')}\n"
        )
        
        if image_analysis:
            prompt += (
                f"\nIMAGE ANALYSIS:\n"
                f"- Diagnosis: {image_analysis.get('image_diagnosis', 'No image diagnosis')}\n"
                f"- Confidence: {image_analysis.get('confidence_score', {})}\n"
            )
        
        prompt += (
            "\nBased on the above, Analyze if there's any combined medical data between text and image\n"
            "Then, provide a comprehensive assessment:"
            "1. Integrated final assessment\n"
            "2. Overall confidence (0-1)\n"
            "3. Recommended next steps\n"
            "4. Any disagreement between analyses"
        )
        
        return await self.run_sync(self._generate_text_sync, prompt, 600, 0.4)

    async def generate_medical_report(self, report_prompt: str) -> str:
        """Generate a comprehensive medical report based on analysis data"""
        prompt = (
            "Generate a structured, professional medical report:\n"
            f"{report_prompt}\n"
            "Include sections: Summary, Observations, Recommendations.\n"
            "Use clinical tone and terminology."
        )
        return await self.run_sync(self._generate_text_sync, prompt, 1024, 0.3)