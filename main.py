import os
import asyncio
import time
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
from typing import List

# Import SDKs
from openai import AsyncOpenAI
from groq import AsyncGroq
import google.generativeai as genai
import cohere

app = FastAPI()

# 1. Initialize ALL Clients
# Note: On Netlify, set these in Site Settings > Environment Variables
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
co = cohere.AsyncClient(api_key=os.getenv("COHERE_API_KEY"))
hf_token = os.getenv("HF_API_KEY") # Hugging Face

class ChatRequest(BaseModel):
    prompt: str
    models: List[str]

# --- PROVIDER ADAPTERS ---

async def call_groq(model: str, prompt: str):
    start = time.time()
    try:
        res = await groq_client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        return {"model": model, "response": res.choices[0].message.content, "latency": round(time.time() - start, 2), "status": "success"}
    except: return {"model": model, "status": "failed"}

async def call_gemini(model: str, prompt: str):
    start = time.time()
    try:
        m = genai.GenerativeModel(model)
        res = m.generate_content(prompt)
        return {"model": model, "response": res.text, "latency": round(time.time() - start, 2), "status": "success"}
    except: return {"model": model, "status": "failed"}

async def call_cohere(model: str, prompt: str):
    start = time.time()
    try:
        res = await co.chat(message=prompt, model=model)
        return {"model": model, "response": res.text, "latency": round(time.time() - start, 2), "status": "success"}
    except: return {"model": model, "status": "failed"}

async def call_huggingface(model: str, prompt: str):
    # Free Serverless Inference API
    import requests
    start = time.time()
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        data = response.json()
        return {"model": model, "response": data[0]['generated_text'], "latency": round(time.time() - start, 2), "status": "success"}
    except: return {"model": model, "status": "failed"}

# --- MAIN ORCHESTRATOR ---

@app.post("/.netlify/functions/main/chat")
async def parallel_chat(request: ChatRequest):
    tasks = []
    for m in request.models:
        # Route to correct provider based on model name
        if "llama" in m or "mixtral" in m or "gemma" in m:
            tasks.append(call_groq(m, request.prompt))
        elif "gemini" in m:
            tasks.append(call_gemini(m, request.prompt))
        elif "command" in m:
            tasks.append(call_cohere(m, request.prompt))
        else:
            tasks.append(call_huggingface(m, request.prompt))

    try:
        # Netlify free tier timeout is strict, we wait 9 seconds max
        results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=9.0)
        return {"results": results}
    except asyncio.TimeoutError:
        return {"error": "Timeout! Some models were too slow for Netlify."}

handler = Mangum(app)