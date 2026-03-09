"""
Unified LLM client — works with both OpenAI API and local Ollama.
All pipeline stages use this instead of importing OpenAI directly.
"""

import json
import logging
import requests
from ingestion.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)

logger = logging.getLogger(__name__)


def llm_chat(system_prompt, user_content, temperature=0.3, max_tokens=800, json_mode=True):
    """
    Send a chat completion request to the configured LLM provider.
    Returns the parsed JSON response (if json_mode) or raw text.

    Works identically whether backed by OpenAI or Ollama.
    """
    if LLM_PROVIDER == "openai":
        return _openai_chat(system_prompt, user_content, temperature, max_tokens, json_mode)
    else:
        return _ollama_chat(system_prompt, user_content, temperature, max_tokens, json_mode)


def _openai_chat(system_prompt, user_content, temperature, max_tokens, json_mode):
    """OpenAI API call (paid, cloud)."""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    kwargs = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content.strip()

    if json_mode:
        return json.loads(text)
    return text


def _ollama_chat(system_prompt, user_content, temperature, max_tokens, json_mode):
    """Ollama local call (free, runs on Mac Mini)."""
    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    if json_mode:
        payload["format"] = "json"

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    text = response.json()["message"]["content"].strip()

    if json_mode:
        # Ollama sometimes wraps JSON in markdown code blocks — clean it
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    return text


def check_ollama_available():
    """Check if Ollama is running and the model is available."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]

        # Check if our configured model is available
        model_base = OLLAMA_MODEL.split(":")[0]
        available = any(model_base in m for m in models)

        if not available:
            print(f"  Model '{OLLAMA_MODEL}' not found in Ollama.")
            print(f"  Available models: {', '.join(models) if models else 'none'}")
            print(f"  Run: ollama pull {OLLAMA_MODEL}")
            return False

        print(f"  Ollama running, model '{OLLAMA_MODEL}' available")
        return True
    except requests.ConnectionError:
        print("  Ollama not running. Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"  Ollama check failed: {e}")
        return False
