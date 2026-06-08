from .base import ModelInterface
from typing import Any, Dict
import asyncio
import functools
from llama_cpp import Llama
import logging
import os
import psutil
import torch

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
                "chat_format": "llama-3",           # For Llama 3.1 models
                "verbose": False,                   # Reduce logging noise
                "n_ctx": 1024,                       # Optimal context for speed (11.41s vs 12.02s)
                "seed": 42,                         # Reproducible results
                "logits_all": False,               # Memory optimization
                "embedding": False,                 # We don't need embeddings
                "n_threads": 4,                     # Optimal CPU threads (best performance: 11.24s)
                "n_threads_batch": 4,               # Optimal batch processing threads
                "mul_mat_q": True,                  # FASTEST: Quantized matrix mult (10.93s)
                "f16_kv": False,                    # FASTEST: FP32 KV cache (11.76s vs 12.42s)
                "numa": False,                      # Single node system
                "use_mmap": True,                   # Memory mapping for efficiency
                "use_mlock": False,                 # Don't lock memory pages
                "n_gpu_layers": 16,                # Optimal GPU layers (tested: 1.8x faster)
                "main_gpu": 0,                     # Use first GPU
                "split_mode": 1,                   # Row-wise split for single GPU
                "n_batch": 512,                    # Optimal batch size (20% faster than 64)
                "n_ubatch": 128,                   # Optimal micro-batch size
                "offload_kqv": True,               # Offload key-query-value to GPU
                "flash_attn": True,                # Enable flash attention for speed
                "low_vram": True,                  # Enable low VRAM mode for efficiency
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

    async def generate_diagnosis(self, symptoms: str) -> str: 
        """High-accuracy diagnosis generation"""
        prompt = f"""Symptoms: {symptoms}
List 5 most possible diagnoses in this exact format:
- diagnosis: <name>
- confidence: <0.0-1.0>

Repeat for each diagnosis."""
        return await self.run_sync(self._generate_text_sync, prompt, 85, 0.1)  

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

    async def generate_overall_instance1(self, symptoms: str, diagnosis: str, confidence: float) -> str:
        """Generate enhanced analysis for textual-only workflow (Instance 1)"""
        
        prompt = f"""
        MEDICAL ANALYSIS

        CONFIRMED DIAGNOSIS: {diagnosis} (Confidence: {confidence:.2f})
        Original Symptoms: {symptoms}
        
        Based on the confirmed diagnosis above, provide output in this EXACT format:                
        - Severity: <mild/moderate/severe/critical>
        - User Explanation: <One simple sentence: {diagnosis} definition>
        - Clinical Reasoning: <detailed medical justification based on user's original symptom ({symptoms}) & confirmed diagnosis ({diagnosis})>
        - Specialist: <choose MOST appropriate specialist type (separate with " / " if there is more than one)>
        
        Keep User Explanation under 25 words. Keep Clinical Reasoning under 50 words and focused on main symptoms only.
        """
        
        return await self.run_sync(self._generate_text_sync, prompt, 400, 0.3)

    async def generate_overall_instance2(self, followup_qna: str, image_diagnosis: str, image_confidence: dict) -> str:
        """Generate analysis for textual + image workflow (Instance 2) - SKIN CANCER SCREENING PATH"""
        
        #Handle confidence scores properly (they're percentages, not decimals), take the highest confidence
        max_confidence = max(image_confidence.values()) if image_confidence and len(image_confidence) > 0 else 0.0
        # Convert to decimal if it's a percentage
        if max_confidence > 1.0:
            max_confidence = max_confidence / 100.0
        
        prompt = f"""
        COMBINED SKIN ANALYSIS

        Follow-up Screening Information:
        {followup_qna}
        
        Image Analysis Results: {image_diagnosis}
        Image Confidence: {max_confidence:.2f}

        Integrate the skin cancer screening responses and image analysis findings, 
        then provide output in this EXACT format:
        - Severity: <mild/moderate/severe/critical>
        - User Explanation: <One simple sentence explaining the skin condition>
        - Clinical Reasoning: <detailed medical justification based on screening responses and image analysis>
        - Specialist: <choose MOST appropriate specialist type (separate with " / " if there is more than one)>
        
        Keep User Explanation under 25 words. Keep Clinical Reasoning under 50 words and focused on skin analysis findings.
        """
        
        return await self.run_sync(self._generate_text_sync, prompt, 500, 0.3)

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
        - User Explanation: <One simple sentence: {diagnosis} definition>
        - Clinical Reasoning: <detailed medical justification based on user's follow-up information & confirmed diagnosis stated above>
        - Specialist: <choose MOST appropriate specialist type (separate with " / " if there is more than one)>
        
        Keep User Explanation under 25 words. Keep Clinical Reasoning under 50 words and focused on main symptoms only.
        """
        
        return await self.run_sync(self._generate_text_sync, prompt, 600, 0.3)

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
        )
        return await self.run_sync(self._generate_text_sync, prompt, 1024, 0.3)
    
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
                
                #Additional cuBLAS optimizations
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