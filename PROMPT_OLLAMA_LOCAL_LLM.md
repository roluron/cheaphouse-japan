# PROMPT À COLLER DANS ANTIGRAVITY — Passer le pipeline LLM sur Ollama local

```
Auto-approve all changes and commands. Don't ask for permission.

The ingestion pipeline currently uses OpenAI's gpt-4o-mini API for 3 stages: translate, lifestyle tagging, and what-to-know generation. This costs ~$0.01/property which gets expensive at scale (100K+ listings).

We're switching to Ollama running locally on a Mac Mini. The user already has Ollama installed. This means ZERO cost for LLM enrichment.

## 1. Update `ingestion/config.py` — add Ollama configuration

Replace the hardcoded OpenAI config with a provider toggle:

```python
import os

# --- LLM Provider Configuration ---
# Set LLM_PROVIDER to "ollama" for local (free) or "openai" for cloud
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")  # Default to Ollama now

# OpenAI settings (cloud, paid)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Ollama settings (local, free)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:14b")
# Good alternatives: "llama3.1:8b", "mistral:7b", "gemma2:9b", "qwen2.5:7b"
# For best Japanese translation: "qwen2.5:14b" (strong multilingual)
# For speed on weaker hardware: "qwen2.5:7b" or "llama3.1:8b"

LLM_BATCH_SIZE = int(os.environ.get("LLM_BATCH_SIZE", "10"))
```

## 2. Create `ingestion/llm_client.py` — unified LLM client

Create a single abstraction that both OpenAI and Ollama can use. This way we only change the client code ONCE and all 3 pipeline stages benefit:

```python
"""
Unified LLM client — works with both OpenAI API and local Ollama.
All pipeline stages use this instead of importing OpenAI directly.
"""

import json
import requests
from config import (
    LLM_PROVIDER,
    OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
)


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
            print(f"⚠ Model '{OLLAMA_MODEL}' not found in Ollama.")
            print(f"  Available models: {', '.join(models) if models else 'none'}")
            print(f"  Run: ollama pull {OLLAMA_MODEL}")
            return False

        print(f"✓ Ollama running, model '{OLLAMA_MODEL}' available")
        return True
    except requests.ConnectionError:
        print("✗ Ollama not running. Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"✗ Ollama check failed: {e}")
        return False
```

## 3. Update `ingestion/pipeline/translate.py`

Replace the direct OpenAI import with our unified client:

Find ALL occurrences of:
```python
from openai import OpenAI
```
and the OpenAI client initialization and API calls.

Replace the LLM call with:
```python
from llm_client import llm_chat

# In the translation function, replace the client.chat.completions.create() block with:
result = llm_chat(
    system_prompt=TRANSLATE_PROMPT,
    user_content=json.dumps(listing_data),
    temperature=0.3,
    max_tokens=800,
    json_mode=True,
)
# result is already parsed JSON with title_en and summary_en
```

Remove the `from openai import OpenAI` import and any `client = OpenAI(...)` initialization.
Remove the `response.choices[0].message.content` parsing — `llm_chat` returns parsed JSON directly.

## 4. Update `ingestion/pipeline/lifestyle.py`

Same pattern — in the `_llm_tags()` function:

Replace the OpenAI client code with:
```python
from llm_client import llm_chat

# In _llm_tags(), replace the API call block with:
result = llm_chat(
    system_prompt=TAG_PROMPT,
    user_content=json.dumps(listing_context),
    temperature=0.2,
    max_tokens=400,
    json_mode=True,
)
# result is already parsed JSON with tags array
```

Remove OpenAI imports and client initialization from this file.

## 5. Update `ingestion/pipeline/quality.py`

Same pattern — in the `_generate_wtk_llm()` function:

Replace the OpenAI client code with:
```python
from llm_client import llm_chat

# In _generate_wtk_llm(), replace the API call block with:
result = llm_chat(
    system_prompt=WHAT_TO_KNOW_PROMPT,
    user_content=json.dumps(listing_data),
    temperature=0.3,
    max_tokens=600,
    json_mode=True,
)
# result is already parsed JSON with whats_attractive, whats_unclear, etc.
```

Remove OpenAI imports and client initialization from this file.

## 6. Update `ingestion/requirements.txt`

Add `requests` if not already there (needed for Ollama HTTP calls):
```
requests>=2.31.0
```

The `openai` package can stay — it's only imported if LLM_PROVIDER is "openai".

## 7. Add Ollama check to CLI

In `ingestion/run.py` (or `cli.py`), add a pre-flight check command:

```python
@cli.command()
def check_llm():
    """Check if the LLM provider is available and ready."""
    from config import LLM_PROVIDER
    print(f"LLM Provider: {LLM_PROVIDER}")

    if LLM_PROVIDER == "ollama":
        from llm_client import check_ollama_available
        if check_ollama_available():
            print("Ready to process listings for FREE!")
        else:
            print("\nTo set up Ollama:")
            print("  1. Start Ollama: ollama serve")
            print("  2. Pull model: ollama pull qwen2.5:14b")
            print("  3. Run pipeline: python run.py pipeline")
    else:
        from config import OPENAI_API_KEY
        if OPENAI_API_KEY:
            print(f"OpenAI API key configured (${OPENAI_API_KEY[:8]}...)")
        else:
            print("⚠ No OPENAI_API_KEY set!")
```

Also add a check at the START of the `pipeline` command — before running any LLM stages, verify Ollama is reachable (if using Ollama provider). If not, print a clear error and exit.

## 8. Update `.env.example`

Add the Ollama config to the example env file:

```bash
# LLM Provider: "ollama" (free, local) or "openai" (paid, cloud)
LLM_PROVIDER=ollama

# Ollama (local) — make sure `ollama serve` is running
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# OpenAI (cloud) — only needed if LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
```

## Model recommendation

For CheapHouse Japan specifically:

1. **Best quality (Japanese understanding):** `qwen2.5:14b` — Alibaba's model, excellent at Japanese text + structured JSON output. ~9GB VRAM. This is the recommended default.

2. **Good balance:** `llama3.1:8b` — Meta's model, solid English output but weaker on Japanese. ~5GB VRAM.

3. **Fastest (weak hardware):** `qwen2.5:7b` — Same Qwen family, half the size. ~4.5GB VRAM.

4. **If Mac Mini has 32GB+ RAM:** `qwen2.5:32b` — Noticeably better quality, still free. Slower but worth it for translation accuracy.

The user should run: `ollama pull qwen2.5:14b` before running the pipeline.

## Speed expectations

- OpenAI gpt-4o-mini: ~0.5-1 second per property (fast, but costs money)
- Ollama qwen2.5:14b on Mac Mini M2: ~3-8 seconds per property (slower, but FREE)
- For 340 properties: ~20-45 minutes total (vs ~3 min on OpenAI but $3-4 cost)
- For 10K properties: ~8-18 hours (but $0 vs ~$100 on OpenAI)

Run overnight for large batches. Zero cost. Perfect for MVP.

## RULES

- The unified `llm_client.py` must handle BOTH providers — pipeline code should NOT import OpenAI directly anymore
- Default provider is now "ollama" (free first, pay later if needed)
- Keep the system prompts IDENTICAL — don't change any prompt text, just the transport layer
- Handle Ollama's JSON quirks (sometimes wraps in markdown code blocks)
- Add timeout handling — Ollama can be slower, use 120s timeout
- If Ollama is not running, show a clear helpful error message, don't crash silently
- Build must pass, push to GitHub
```
