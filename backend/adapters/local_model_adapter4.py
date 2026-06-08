from .base import ModelInterface
from typing import Any, Dict
import asyncio
import functools
from llama_cpp import Llama
import logging
import os
import psutil
import torch
import math
import re

logger = logging.getLogger(__name__)

class LocalModelAdapter(ModelInterface):  
    def __init__(self, 
                 llm_path: str):
        self.model_path = llm_path
        self.model = None
        
        # System detection for optimal configuration
        self.gpu_available = torch.cuda.is_available()
        self.gpu_memory_gb = self._get_gpu_memory() if self.gpu_available else 0
        self.cpu_cores = psutil.cpu_count(logical=False)
        self.system_ram_gb = psutil.virtual_memory().total / (1024**3)
        
        logger.info(f"🔧 Local Model Adapter System Info:")
        logger.info(f"   GPU Available: {self.gpu_available}")
        logger.info(f"   GPU Memory: {self.gpu_memory_gb:.1f}GB")
        logger.info(f"   CPU Cores: {self.cpu_cores}")
        logger.info(f"   System RAM: {self.system_ram_gb:.1f}GB")
    
    def _get_gpu_memory(self) -> float:
        """Get available GPU memory in GB"""
        try:
            if torch.cuda.is_available():
                gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
                return gpu_memory_bytes / (1024**3)
            return 0.0
        except Exception:
            return 0.0
        
    async def load_model(self):
        """Load model with FAST + LOW MEMORY settings for RTX 3050 cuBLAS"""
        try:
            logger.info("🚀 Loading Llama 3.1 UltraMedical 8B with FAST + LOW MEMORY cuBLAS...")
            
            # Enable speed mode before loading
            self.enable_speed_mode()
            
            # Get optimal settings based on system capabilities
            """Optimized settings for FAST + LOW MEMORY inference with cuBLAS GPU acceleration"""
            settings = {
                "chat_format": "llama-3",   # Selects prompt/template parsing compatible with Llama 3 chat tokens.
                "verbose": False,           # Disables detailed llama.cpp runtime logs.
                "n_ctx": 1024,              # Maximum context window (prompt + generated tokens) in tokens.
                "seed": 42,                 # Sets RNG seed for reproducible sampling behavior.
                "logits_all": False,        # Returns logits only for generated tokens (saves memory/compute).
                "embedding": False,         # Disables embedding mode; model is used for generation only.
                "n_threads": 4,             # CPU threads used for token generation work.
                "n_threads_batch": 4,       # CPU threads used during prompt/batch processing.
                "mul_mat_q": True,          # Enables quantized matrix multiplication optimizations.
                "f16_kv": False,            # KV cache precision toggle (False = FP32 cache, higher memory use).
                "numa": False,              # Disables NUMA-aware memory placement (single-socket systems usually fine).
                "use_mmap": True,           # Memory-maps model file to reduce RAM load time/copies.
                "use_mlock": False,         # Does not lock model pages in RAM (avoids elevated memory pressure).
                "n_gpu_layers": 16,         # Number of transformer layers offloaded to GPU.
                "main_gpu": 0,              # GPU device index to use as primary offload target.
                "split_mode": 1,            # Tensor split strategy across GPUs (row split; relevant for multi-GPU too).
                "n_batch": 512,             # Logical batch size for prompt evaluation throughput.
                "n_ubatch": 128,            # Micro-batch chunk size used internally to fit compute/memory.
                "offload_kqv": True,        # Offloads attention K/Q/V operations to GPU when possible.
                "flash_attn": True,         # Enables Flash Attention kernels for faster/lower-memory attention.
                "low_vram": True,           # Activates lower-VRAM allocation strategy (can reduce speed in some setups).
            }
            
            self.model = Llama(
                model_path=self.model_path,
                **settings
            )
            
            # Apply additional optimizations
            self.optimize_for_inference()
            
            logger.info("✅ Model loaded successfully with FAST + LOW MEMORY cuBLAS")
            logger.info(f"   Model: {os.path.basename(self.model_path)}")
            logger.info(f"   GPU Acceleration: {self.gpu_available}")
            logger.info(f"   GPU Layers: {settings.get('n_gpu_layers', 0)}")
            logger.info(f"   Context Length: {settings.get('n_ctx', 'unknown')}")
            logger.info(f"   Low VRAM Mode: {settings.get('low_vram', False)}")
            logger.info(f"   Memory Usage: {self._get_memory_usage()}")
                
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            raise
    
    def _get_memory_usage(self) -> str:
        """Get current memory usage statistics"""
        try:
            if self.gpu_available:
                gpu_allocated = torch.cuda.memory_allocated(0) / (1024**3)
                gpu_cached = torch.cuda.memory_reserved(0) / (1024**3)
                return f"GPU: {gpu_allocated:.2f}GB allocated, {gpu_cached:.2f}GB cached"
            else:
                ram_used = psutil.virtual_memory().used / (1024**3)
                return f"RAM: {ram_used:.2f}GB used"
        except Exception:
            return "Memory stats unavailable"

    async def run_sync(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        #ThreadPoolExecutor for better control
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            func_with_kwargs = functools.partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, func_with_kwargs)

    def _generate_text_sync(self, prompt: str, max_tokens: int = 512, temperature: float = None) -> str:
        """Synchronous text generation optimized for SPEED + LOW MEMORY"""
        try:
            if not self.model:
                raise ValueError("Model not loaded")
            
            formatted_prompt = self._format_prompt(prompt)
            
            # Speed-optimized generation parameters
            response = self.model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature or 0.1,    # Even lower temp for faster generation
                top_p=0.7,                          # Further reduced for speed
                top_k=15,                           # Further reduced for speed
                repeat_penalty=1.02,                # Lower penalty for speed
                stop=["<|eot_id|>", "<|end_of_text|>"],
                echo=False,                         # Don't echo the prompt
                stream=False,                       # Non-streaming for simplicity
            )
            
            if response and response.get('choices'):
                result = response['choices'][0]['text'].strip()
                return result
            else:
                logger.warning("Empty response from llama-cpp-python generation")
                return ""
            
        except Exception as e:
            logger.error(f"Llama-cpp-python text generation error: {e}")
            return ""
        
    def _format_prompt(self, user_input: str) -> str:
        """Consistent prompt format"""
        system_prompt = (
            "You are an AI medical assistant. Provide accurate, structured responses.\n"
            "Always follow the exact format requested.\n"
            "Be concise and professional.\n"
        )
        
        return (
            "<|start_header_id|>system<|end_header_id|>\n"
            f"{system_prompt}<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n"
            f"{user_input}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n"
        )
        
    # =============================================================================
    # CONFIDENCE CALCULATION METHODS
    # =============================================================================

    def _calculate_diagnosis_specificity(self, diagnosis: str) -> float:
        """Calculate how specific/detailed the diagnosis is"""
        # More words = more specific
        word_count = len(diagnosis.split())
        
        # Medical terminology indicators
        medical_terms = ['syndrome', 'disease', 'disorder', 'condition', 'infection', 
                        'deficiency', 'inflammation', 'acute', 'chronic', 'primary', 'secondary']
        has_medical_terms = any(term.lower() in diagnosis.lower() for term in medical_terms)
        
        # Specificity indicators
        specificity_indicators = ['stage', 'grade', 'type', 'variant', 'sub', 'mild', 'severe', 'moderate']
        has_specificity = any(ind.lower() in diagnosis.lower() for ind in specificity_indicators)
        
        score = 0.5  # Base score
        score += min(0.3, word_count * 0.05)  # Word count bonus
        score += 0.15 if has_medical_terms else 0
        score += 0.1 if has_specificity else 0
        
        return min(1.0, score)

    def _calculate_symptom_alignment(self, diagnosis: str, symptoms: str) -> float:
        """Calculate how well diagnosis aligns with reported symptoms"""
        if not symptoms:
            return 0.5
        
        # Simple keyword matching (can be enhanced with medical ontologies)
        symptom_keywords = symptoms.lower().split()
        diagnosis_keywords = diagnosis.lower().split()
        
        # Common medical condition keywords
        alignment_keywords = {
            'chest pain': ['heart', 'cardiac', 'angina', 'myocardial', 'coronary'],
            'headache': ['migraine', 'tension', 'cluster', 'neurological'],
            'fever': ['infection', 'inflammatory', 'viral', 'bacterial'],
            'cough': ['respiratory', 'bronchitis', 'pneumonia', 'asthma'],
            'fatigue': ['anemia', 'thyroid', 'depression', 'chronic'],
            'skin': ['dermatitis', 'eczema', 'psoriasis', 'rash', 'lesion']
        }
        
        alignment_score = 0.5  # Base alignment
        
        # Check for direct keyword matches
        for symptom_word in symptom_keywords:
            if any(symptom_word in diag_word for diag_word in diagnosis_keywords):
                alignment_score += 0.1
        
        # Check medical condition alignments
        for symptom_phrase, related_terms in alignment_keywords.items():
            if symptom_phrase in symptoms.lower():
                if any(term in diagnosis.lower() for term in related_terms):
                    alignment_score += 0.15
        
        return min(1.0, alignment_score)

    def _get_condition_commonality(self, diagnosis: str) -> float:
        """Get commonality score (common conditions = higher confidence)"""
        common_conditions = [
            'common cold', 'flu', 'hypertension', 'diabetes', 'migraine', 'tension headache', 'gastritis',
            'bronchitis', 'pneumonia', 'urinary tract infection', 'allergic rhinitis', 'asthma',
            'eczema', 'anemia', 'depression', 'anxiety', 'otitis media', 'sinusitis', 'conjunctivitis',
            'gastroenteritis', 'osteoarthritis', 'back pain', 'hyperlipidemia', 'obesity', 'hypothyroidism',
            'upper respiratory infection', 'acute pharyngitis', 'acute tonsillitis', 'acute otitis externa',
            'acute sinusitis', 'acute bronchitis', 'acute gastroenteritis', 'acute cystitis', 'acute laryngitis',
            'acute conjunctivitis', 'acute dermatitis', 'acute urticaria', 'acute allergic reaction',
            'acute viral infection', 'acute bacterial infection', 'sprain', 'strain', 'muscle pain',
            'tension-type headache', 'seasonal allergies', 'indigestion', 'heartburn', 'constipation',
            'diarrhea', 'insomnia', 'fatigue', 'menstrual cramps', 'acne', 'dandruff'
        ]
        
        rare_conditions = [
            'lupus', 'multiple sclerosis', 'rare genetic', 'exotic',
            'zebra diagnosis', 'uncommon', 'atypical',
            'amyloidosis', 'sarcoidosis', 'porphyria', 'prion disease',
            'ehlers-danlos', 'marfan syndrome', 'wilson disease', 'gauchers disease',
            'fabry disease', 'tay-sachs', 'kawasaki disease', 'behcet disease',
            'goodpasture syndrome', 'churg-strauss', 'wegener granulomatosis',
            'sjogren syndrome', 'myasthenia gravis', 'lambert-eaton', 'paraneoplastic',
            'idiopathic pulmonary fibrosis', 'idiopathic thrombocytopenic purpura',
            'pemphigus vulgaris', 'dermatomyositis', 'polymyositis', 'stiff person syndrome',
            'progressive multifocal leukoencephalopathy', 'creutzfeldt-jakob', 'alport syndrome',
            'retinitis pigmentosa', 'hereditary angioedema', 'familial mediterranean fever',
            'moyamoya disease', 'takayasu arteritis', 'polyarteritis nodosa', 'giant cell arteritis',
            'granulomatosis with polyangiitis', 'anti-glomerular basement membrane disease',
            'cryoglobulinemia', 'lymphangioleiomyomatosis', 'tuberous sclerosis', 'sturge-weber syndrome',
            'von hippel-lindau', 'neurofibromatosis', 'pseudoxanthoma elasticum', 'blue rubber bleb nevus syndrome'
        ]
        
        diagnosis_lower = diagnosis.lower()
        
        if any(common in diagnosis_lower for common in common_conditions):
            return 0.8  # High confidence for common conditions
        elif any(rare in diagnosis_lower for rare in rare_conditions):
            return 0.4  # Lower confidence for rare conditions
        else:
            return 0.6  # Medium confidence for others

    def _assess_diagnosis_quality(self, diagnosis: str) -> float:
        """Assess the quality of the diagnosis text"""
        # Check for vague terms that reduce confidence
        vague_terms = ['possible', 'maybe', 'could be', 'might be', 'uncertain', 'unclear', 'I think', 'I feel', 'probably', 'possibly']
        has_vague_terms = any(term in diagnosis.lower() for term in vague_terms)
        
        # Check for confident language
        confident_terms = ['definitely', 'certain', 'verified', 'confirmed', 'definitive', 'classic', 'typical', 'characteristic', 'observed']
        has_confident_terms = any(term in diagnosis.lower() for term in confident_terms)
        
        score = 0.7  # Base quality score
        score -= 0.2 if has_vague_terms else 0
        score += 0.15 if has_confident_terms else 0
        
        return max(0.3, min(1.0, score))

    def _calculate_enhanced_confidence(self, diagnosis_text: str, position: int, temperature: float, 
                                     total_diagnoses: int, symptoms: str) -> float:
        """Calculate confidence using multiple medical factors"""
        
        # 1. Position factor (exponential decay instead of linear)
        position_factor = 0.95 ** position  # 0.95, 0.90, 0.86, 0.81, 0.77
        
        # 2. Temperature factor (more sophisticated mapping)
        temp_factor = max(0.6, 1.0 - (temperature * 1.5))
        
        # 3. Specificity factor (more specific = higher confidence)
        specificity_score = self._calculate_diagnosis_specificity(diagnosis_text)
        
        # 4. Symptom alignment factor
        alignment_score = self._calculate_symptom_alignment(diagnosis_text, symptoms)
        
        # 5. Medical commonality factor
        commonality_score = self._get_condition_commonality(diagnosis_text)
        
        # 6. Diagnosis quality factor
        quality_score = self._assess_diagnosis_quality(diagnosis_text)
        
        # Weighted combination
        base_confidence = (
            position_factor * 0.25 +      # Position weight
            temp_factor * 0.20 +          # Temperature weight  
            specificity_score * 0.20 +    # Specificity weight
            alignment_score * 0.15 +      # Symptom alignment weight
            commonality_score * 0.10 +    # Commonality weight
            quality_score * 0.10          # Quality weight
        )
        
        # Apply confidence decay for lower positions
        if position >= 2:  # 3rd diagnosis onwards
            base_confidence *= (0.85 ** (position - 1))
        
        return max(0.25, min(0.92, base_confidence))

    def _generate_with_confidences_sync(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> str:
        """Generate diagnoses with enhanced fallback confidence calculation."""
        if not self.model:
            raise ValueError("Model not loaded")

        # Modify the prompt to exclude confidence in generation
        prompt_no_conf = re.sub(r"-\s*confidence.*?<0.0-1.0>", "", prompt, flags=re.IGNORECASE)
        formatted_prompt = self._format_prompt(prompt_no_conf)

        logger.info("Using blackbox-based confidence calculation (logprobs disabled)")
        
        response = self.model(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.7,
            top_k=15,
            repeat_penalty=1.02,
            stop=["<|eot_id|>", "<|end_of_text|>"],
            echo=False,
            # logprobs=True, Only for logits_all = True in settings (which uses whitebox method for confidence calculation)
        )

        if not response or "choices" not in response:
            logger.warning("Empty response from llama-cpp-python generation")
            return ""

        raw_text = response["choices"][0]["text"].strip()

        # Find diagnosis lines and apply enhanced confidence calculation
        diag_pattern = re.compile(r"^\s*-\s*diagnosis\s*:\s*(.+)$", re.IGNORECASE)
        lines = raw_text.splitlines()
        diagnosis_indices = [i for i, line in enumerate(lines) if diag_pattern.match(line)]

        # Extract original symptoms from the prompt for alignment calculation
        symptoms_match = re.search(r"Symptoms:\s*(.+?)(?:\n|$)", prompt_no_conf, re.IGNORECASE)
        original_symptoms = symptoms_match.group(1) if symptoms_match else ""

        # Apply enhanced confidence calculation to each diagnosis
        for idx in reversed(range(len(diagnosis_indices))):
            diag_idx = diagnosis_indices[idx]
            diagnosis_text = lines[diag_idx].split(":", 1)[1].strip() if ":" in lines[diag_idx] else ""
            
            # Calculate enhanced confidence using your sophisticated algorithm
            enhanced_confidence = self._calculate_enhanced_confidence(
                diagnosis_text, idx, temperature, len(diagnosis_indices), original_symptoms
            )
            
            # Insert confidence line after diagnosis line
            lines.insert(diag_idx + 1, f"- confidence: {enhanced_confidence:.3f}")

        return "\n".join(lines)
    
    # =============================================================================
    # PUBLIC API METHODS
    # =============================================================================
    
    async def generate_diagnosis(self, symptoms: str) -> str: 
        """High-accuracy diagnosis generation"""
        prompt = f"""Symptoms: {symptoms}
List 5 most possible diagnoses in this exact format ONLY:
- diagnosis: <name>

Repeat for each diagnosis."""
        return await self.run_sync(self._generate_with_confidences_sync, prompt, 65, 0.1)
    
    async def generate_text_guidance(self, prompt: str, max_tokens: int = 200, temperature: float = 0.2) -> str:
        """Generate short, focused guidance text - NO additional formatting needed"""
        
        # The prompt is already formatted in _generate_dynamic_content, so pass it directly
        return await self.run_sync(self._generate_text_sync, prompt, max_tokens, temperature)
    

#     async def generate_followup_questions(self, diagnosis_context: str, average_confidence: float) -> str:
#         """Generate follow-up questions based on diagnosis context and confidence"""
        
#     #     prompt = f"""
#     # Based on suspected condition(s): {diagnosis_context}

#     # Generate ONLY 5 focused follow-up questions to help clarify the diagnosis.

#     # Confidence level: {average_confidence:.2f} 

#     # Questions should cover:
#     # 1. Symptom duration/progression
#     # 2. Associated symptoms
#     # 3. Medical history
#     # 4. Triggers/patterns  
#     # 5. Severity/impact

#     # Format as numbered questions (1., 2., 3., etc.).
#     # """
#         prompt = f"""Based on: {diagnosis_context} (confidence: {average_confidence:.2f})
# Generate 5 follow-up questions numbered 1-5:
# 1. 
# 2. 
# 3. 
# 4. 
# 5. """
        
#         return await self.run_sync(self._generate_text_sync, prompt, 150, 0.1) 

    # education_prompt = f"""Create patient education for {diagnosis}:
    # WHAT IS IT: [simple definition in 20 words]
    # CAUSES: [main causes in 15 words]
    # PROGNOSIS: [typical outlook in 20 words]
    # SELF-CARE: [practical tips in 25 words]

    # Use simple, non-medical language."""

    async def generate_overall_instance1(self, symptoms: str, diagnosis: str, confidence: float) -> str:
        """Generate enhanced analysis for textual-only workflow (Instance 1)"""
        
        prompt = f"""
        MEDICAL ANALYSIS

        CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})
        Original Symptoms: {symptoms}
        
        Based on the confirmed diagnosis above, provide output in this EXACT format:                
        - Severity: <mild/moderate/severe/critical>
        - User Explanation: <Simple definition of {diagnosis} and its main causes>
        - Clinical Reasoning: <detailed medical justification based on user's original symptom ({symptoms}) & confirmed diagnosis ({diagnosis})>
        - Specialist: <choose MOST appropriate specialist type (separate with " / " if there is more than one)>
        
        Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words and focused on main symptoms only.
        """
        
        return await self.run_sync(self._generate_text_sync, prompt, 400, 0.3)

    async def generate_overall_instance2(self, followup_qna: str, image_diagnosis: str, image_confidence_scores: dict, max_confidence,risk_context: str = "") -> str:
        """Generate analysis for textual + image workflow (Instance 2) - SKIN CANCER SCREENING PATH"""
        
        prompt = f"""
    COMPREHENSIVE SKIN LESION ANALYSIS

    PATIENT SCREENING RESPONSES:
    {followup_qna}

    {risk_context}

    IMAGE ANALYSIS RESULTS:
    - AI Image Diagnosis: {image_diagnosis}
    - Image Confidence: {max_confidence:.1f}%
    - All Image Predictions: {dict(sorted(image_confidence_scores.items(), key=lambda x: x[1], reverse=True))}

    INTEGRATION INSTRUCTIONS:
    Synthesize the ABCDE screening responses, risk assessment, and image analysis to determine the most appropriate diagnosis. Consider:
    1. Do the ABCDE findings support the image diagnosis?
    2. Does patient history/symptoms align with image findings?
    3. Are there any contradictions that need resolution?
    4. What is the most clinically appropriate diagnosis considering all evidence?

    Provide output in this EXACT format:
    - Final Diagnosis: <most appropriate diagnosis considering ALL evidence>
    - Confidence: <0.0-1.0 based on evidence concordance>
    - Severity: <mild/moderate/severe/critical>
    - User Explanation: <Explanation of the diagnosed skin condition>
    - Clinical Reasoning: <detailed justification integrating screening, ABCDE, and image findings>
    - Specialist: <appropriate specialist>

    Keep explanations under 30 words, reasoning under 80 words.
    """
        
        return await self.run_sync(self._generate_text_sync, prompt, 600, 0.3)

    async def generate_overall_instance3(self, followup_qna: str, enhanced_diagnosis: str, enhanced_confidence: float) -> str:
        """Generate analysis for textual + follow-up workflow (Instance 3)"""
        
        confidence = enhanced_confidence if enhanced_confidence is not None else 0.0
        diagnosis = enhanced_diagnosis if enhanced_diagnosis is not None else "Unknown condition"
        followup = followup_qna if followup_qna is not None else "No follow-up information available"
        
        prompt = f"""
        ENHANCED MEDICAL ANALYSIS

        Follow-up Information:
        {followup}

        CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})

        Based on the confirmed diagnosis above, provide output in this EXACT format:                
        - Severity: <mild/moderate/severe/critical>
        - User Explanation: <Simple definition of {diagnosis} and its main causes>
        - Clinical Reasoning: <detailed medical justification based on user's follow-up information & confirmed diagnosis stated above>
        - Specialist: <choose MOST appropriate specialist type (separate with " / " if there is more than one)>
        
        Keep User Explanation around 50 words. Keep Clinical Reasoning under 60 words and focused on main symptoms only.
        """
        
        return await self.run_sync(self._generate_text_sync, prompt, 300, 0.3)

    # async def generate_overall_instance4(self, followup_overall: str, followup_diagnosis: Dict, skin_symptoms: str, image_analysis: Dict) -> str:
    #     """Generate comprehensive analysis for all data workflow (Instance 4)"""
        
    #     image_diagnosis = image_analysis.get("image_diagnosis", "No image diagnosis")
    #     image_confidence = image_analysis.get("confidence_score", {})
    #     max_image_conf = max(image_confidence.values()) / 100 if image_confidence else 0.0
        
    #     prompt = f"""
    #     COMPREHENSIVE MEDICAL ANALYSIS
        
    #     Follow-up Responses:
    #     {followup_overall}        

    #     Follow-up Diagnosis: {followup_diagnosis.get("text_diagnosis", "Unknown")}
    #     Follow-up Confidence: {followup_diagnosis.get("diagnosis_confidence", 0.0):.2f}
        
    #     Skin Symptoms: {skin_symptoms}
    #     Image Diagnosis: {image_diagnosis}
    #     Image Confidence: {max_image_conf:.2f}
        
    #     Integrate all information and provide output in this EXACT format:        
    #     - Final Diagnosis: [most comprehensive diagnosis]
    #     - Confidence: [0.0-1.0]
    #     - Severity: [mild/moderate/severe/critical]
    #     - User Explanation: [Simple, clear explanation of the diagnosis in one sentence.]
    #     - Clinical Reasoning: [Technical justification: why this diagnosis was chosen based on symptom analysis, confidence factors, diagnostic criteria, and clinical evidence from the initial symptoms provided]
    #     - Specialist: [single term: cardiologist/dermatologist/neurologist/general_practitioner and more]
    #     """
        
    #     return await self.run_sync(self._generate_text_sync, prompt, 800, 0.3)

    async def generate_medical_report(self, report_prompt: str) -> str:
        """Generate a comprehensive medical report based on analysis data"""
        prompt = (
            "Generate a structured, professional medical report:\n"
            f"{report_prompt}\n"
            "Include sections: Summary, Observations, Recommendations.\n"
            "Use clinical tone and terminology."
        )
        return await self.run_sync(self._generate_text_sync, prompt, 1024, 0.3)
    
    # =============================================================================
    # PERFORMANCE AND OPTIMIZATION METHODS
    # =============================================================================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics for cuBLAS optimization"""
        stats = {
            "framework": "llama-cpp-python + cuBLAS",
            "optimization": "FAST + LOW MEMORY",
            "gpu_available": self.gpu_available,
            "gpu_memory_gb": self.gpu_memory_gb,
            "cpu_cores": self.cpu_cores,
            "system_ram_gb": self.system_ram_gb,
            "model_loaded": self.model is not None,
            "memory_usage": self._get_memory_usage(),
        }
        
        if self.gpu_available:
            try:
                stats.update({
                    "gpu_allocated_gb": torch.cuda.memory_allocated(0) / (1024**3),
                    "gpu_cached_gb": torch.cuda.memory_reserved(0) / (1024**3),
                    "gpu_utilization": self._get_gpu_utilization(),
                    "cublas_enabled": "Yes (optimized for RTX 3050)",
                })
            except Exception:
                pass
        
        # Llama.cpp specific stats
        if self.model:
            try:
                stats.update({
                    "n_ctx": getattr(self.model, "_n_ctx", "unknown"),
                    "n_gpu_layers": getattr(self.model, "_n_gpu_layers", "unknown"),
                    "batch_size": getattr(self.model, "_n_batch", "unknown"),
                    "low_vram_mode": "enabled" if self.gpu_available else "disabled",
                })
            except Exception:
                pass
        
        return stats
    
    def _get_gpu_utilization(self) -> float:
        """Get GPU utilization percentage"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return utilization.gpu
        except Exception:
            return 0.0
    
    def optimize_for_inference(self):
        """Apply runtime optimizations for FAST + LOW MEMORY inference"""
        try:
            if self.gpu_available:
                # Clear GPU cache for optimal memory usage
                torch.cuda.empty_cache()
                
                # Additional cuBLAS optimizations
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                torch.backends.cudnn.benchmark = True
                
                logger.info("🧹 GPU cache cleared + cuBLAS optimizations applied")
                logger.info("⚡ TF32 enabled for maximum speed on RTX 3050")
        except Exception as e:
            logger.warning(f"Optimization failed: {e}")
    
    def enable_speed_mode(self):
        """Enable maximum speed mode for inference"""
        if self.gpu_available:
            try:
                # Set CUDA to performance mode
                torch.cuda.set_per_process_memory_fraction(0.9)
                
                # Enable fast math for cuBLAS
                torch.backends.cuda.fast_math = True
                
                logger.info("🚀 Speed mode enabled - maximum performance")
            except Exception as e:
                logger.warning(f"Speed mode setup failed: {e}")