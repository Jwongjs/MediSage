"""
Quick test for optimized LocalModelAdapter
"""
import asyncio
import time
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.adapters.local_model_adapter4 import LocalModelAdapter

async def test_optimized_adapter():
    print("🚀 Testing GPU-Optimized LocalModelAdapter")
    print("=" * 50)
    
    # Initialize adapter with model path
    model_path = os.path.join('ai_models', 'Llama-3.1-8B-UltraMedical.Q8_0.gguf')
    adapter = LocalModelAdapter(llm_path=model_path)
    
    # Load model and measure time
    print("Loading model...")
    start_time = time.time()
    await adapter.load_model()
    load_time = time.time() - start_time
    print(f"⏱️  Model load time: {load_time:.2f}s")
    
    # # Test simple generation
    # print("\nTesting simple generation...")
    # start_time = time.time()
    # result = await adapter.run_sync(
    #     adapter.model,
    #     "What is diabetes?",
    #     max_tokens=20,
    #     temperature=0.1
    # )
    # gen_time = time.time() - start_time
    # print(f"⏱️  Simple generation: {gen_time:.2f}s")
    # print(f"📝 Result: {result['choices'][0]['text'] if result.get('choices') else 'N/A'}")
    
    # Test medical diagnosis
    print("\nTesting medical diagnosis...")
    start_time = time.time()
    diagnosis = await adapter.generate_diagnosis('chest pain, shortness of breath')
    diag_time = time.time() - start_time
    print(f"⏱️  Diagnosis time: {diag_time:.2f}s")
    print(f"📝 Diagnosis: {diagnosis}...")
    
    # Performance summary
    print("\n🎯 PERFORMANCE SUMMARY:")
    print(f"   Load time: {load_time:.2f}s")
    # print(f"   Simple gen: {gen_time:.2f}s")
    print(f"   Diagnosis: {diag_time:.2f}s")
    
    # if gen_time <= 5.0:
    #     print("✅ GPU acceleration working! Under 5s target")
    # else:
    #     print("⚠️  Performance could be improved")
    
    # Get performance stats
    stats = adapter.get_performance_stats()
    print(f"\n📊 GPU Stats:")
    print(f"   GPU Available: {stats.get('gpu_available', 'Unknown')}")
    print(f"   GPU Memory: {stats.get('gpu_memory_gb', 'Unknown')}GB")
    print(f"   cuBLAS Enabled: {stats.get('cublas_enabled', 'Unknown')}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_optimized_adapter())