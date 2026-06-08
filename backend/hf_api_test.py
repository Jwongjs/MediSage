from dotenv import load_dotenv
import os
import asyncio
from backend.adapters.hf_api_adapter import HuggingFaceAdapter
from PIL import Image

load_dotenv()

async def main():
    api_key = os.getenv("hf_api2")
    if not api_key:
        print("Error: Hugging Face API key not found. Set hf_api in your .env file.")
        return

    # --- IMPORTANT ---
    # Replace these with actual Hugging Face model IDs you want to test.
    # For example:
    model_id = "https://huggingface.co/aaditya/Llama3-OpenBioLLM-70B" #mistralai/Mistral-7B-Instruct-v0.1
    #
    # For text generation tasks (chat, plan_and_call_tools, summary_to_report, generate_diagnosis),
    # ensure you choose models capable of text generation.
    # For `generate_diagnosis`, you might need a medically fine-tuned generative model.
    # For `imageClassification_model`, choose an image classification model.
    # For `embedding_model`, choose a sentence embedding model.

    adapter = HuggingFaceAdapter(
        multipurpose_model=model_id,
        api_key=api_key
    )

    print("Testing HuggingFaceAdapter (with streaming)...\n")

    # Test chat (streaming)
    print("--- Testing chat (streaming) ---")
    full_chat_response = ""
    print("Chat response: ", end="")
    # Since hf_adapter.chat will now return a string (matching base.py)
    full_chat_response = await adapter.chat("Hello, how are you today? Tell me a short story.")
    print(f"Chat response: {full_chat_response}\n")
    print("\n--- End of chat ---\n")
    # print(f"Aggregated chat response: {full_chat_response}\n") # Optional: print full response

    #Test plan_and_call_tools (internally aggregates, so await as before)
    print("--- Testing plan_and_call_tools ---")
    tools_plan = await adapter.plan_and_call_tools(
        "What's the weather in London and book a meeting for tomorrow?", 
        ["search_weather", "google_calendar_book_meeting"]
        )
    print(f"Tools plan: {tools_plan}\n")
    print("\n--- End of planning and calling of tools ---\n")

    # Test summary_to_report (streaming)
    print("--- Testing summary_to_report ---")
    # Since hf_adapter.summary_to_report will now return a string
    full_report_response = await adapter.summary_to_report("Patient felt dizzy and had a headache.", "Possible migraine.")
    print(f"Report: {full_report_response}\n")
    print("\n--- End of summary_to_report ---\n")

    # Test generate_diagnosis (streaming) -> Now non-streaming, direct await
    print("--- Testing generate_diagnosis ---")
    # Since hf_adapter.generate_diagnosis will now return a string
    full_diagnosis_response = await adapter.generate_diagnosis("Symptoms: fever, cough, and sore throat.")
    print(f"Diagnosis: {full_diagnosis_response}\n")
    print("\n--- End of generate_diagnosis ---\n")
    
if __name__ == "__main__":
    asyncio.run(main())