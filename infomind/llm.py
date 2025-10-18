from openai import OpenAI
import requests


def start_chat(api_key, bot_id):
    url = "https://api.metisai.ir/api/v1/chat/session"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "botId": bot_id,
        "user": None,
        "initialMessages": [
            {
                "type": "USER",
                "content": ""
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print("❌ Metis API Error:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        raise Exception("Failed to get response from Metis API.")
    
    session_id = response.json()["id"]

    return session_id


import os
import logging
from typing import Optional
import requests

try:
    from dotenv import load_dotenv
except Exception:
    # dotenv is optional; we will still try to read environment variables
    def load_dotenv(path=None):
        return None


logger = logging.getLogger(__name__)


def _load_config(env_path: Optional[str] = None) -> dict:
    """Load API key and bot id from environment or .env file.

    Supports both standard KEY=VALUE and simple python-like assignments
    (e.g. api_key = "...").
    """
    # Try dotenv first (will populate os.environ)
    try:
        load_dotenv(env_path)
    except Exception:
        pass

    # Common names
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or os.getenv("api_key")
    bot_id = os.getenv("BOT_ID") or os.getenv("bot_id")

    # Fallback: attempt to parse .env manually if present and keys not set
    if (not api_key or not bot_id) and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                    elif "=" not in line and " " in line and "api_key" in line:
                        # handle lines like: api_key = "value"
                        parts = line.split("=", 1)
                        k, v = parts[0].strip(), parts[1].strip()
                    else:
                        continue
                    k = k.strip().strip('"').strip("'")
                    v = v.strip().strip('"').strip("'")
                    if not api_key and k.lower() in ("openai_api_key", "api_key", "openai"):
                        api_key = v
                    if not bot_id and k.lower() in ("bot_id", "botid"):
                        bot_id = v
        except Exception as e:
            logger.debug(f"Failed to parse .env: {e}")

    return {"api_key": api_key, "bot_id": bot_id}


def start_chat(api_key: str, bot_id: str) -> str:
    """Start a new chat session using the Metis-style API and return session id."""
    url = "https://api.metisai.ir/api/v1/chat/session"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "botId": bot_id,
        "user": None,
        "initialMessages": [{"type": "USER", "content": ""}],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        logger.error("Metis start_chat failed: %s %s", resp.status_code, resp.text)
        raise RuntimeError(f"start_chat failed: {resp.status_code} {resp.text}")

    data = resp.json()
    # API returns id field for session
    session_id = data.get("id") or data.get("sessionId")
    if not session_id:
        raise RuntimeError("start_chat response missing session id")

    return session_id


def continue_session(api_key: str, session_id: str, query: str) -> str:
    """Send a user message to an existing session and return the assistant text."""
    url = f"https://api.metisai.ir/api/v1/chat/session/{session_id}/message"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"message": {"content": query, "type": "USER"}}

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        logger.error("Metis continue_session failed: %s %s", resp.status_code, resp.text)
        raise RuntimeError(f"continue_session failed: {resp.status_code} {resp.text}")

    data = resp.json()
    # Depending on API shape, the assistant content might be nested.
    # Try common patterns.
    if isinstance(data, dict):
        # direct content
        if "content" in data:
            return data["content"]
        # message object
        if "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content") or data["message"].get("text")
        # choices-like
        if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
            ch = data["choices"][0]
            if isinstance(ch, dict):
                return ch.get("text") or ch.get("message", {}).get("content") or ""

    # fallback to raw text
    return resp.text


def generate_reply(prompt: str, env_path: Optional[str] = None) -> str:
    """Convenience helper: load api config, start session, send prompt, return assistant reply."""
    cfg = _load_config(env_path)
    api_key = cfg.get("api_key")
    bot_id = cfg.get("bot_id")
    if not api_key or not bot_id:
        raise RuntimeError("Missing api_key or bot_id. Set them in environment or .env")

    session_id = start_chat(api_key, bot_id)
    reply = continue_session(api_key, session_id, prompt)
    return reply


def continue_session(api_key, session_id, query):
    url = f"https://api.metisai.ir/api/v1/chat/session/{session_id}/message"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "content": query,
            "type": "USER"
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("❌ Error sending message:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception("Failed to send message to Metis session.")

    return response.json()["content"]