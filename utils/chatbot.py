# utils/chatbot.py

import os
import re
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# ---- Make repo root importable for gpt_prompts (same intent as your prior sys.path.append) ----
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# These prompts are your own; we keep your import path
from gpt_prompts import (
    PHQ9_SUMMARY_PROMPT,
    GAD7_SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    SAFETY_CHECK_PROMPT,
    SYSTEM_INSTRUCTION,
    MOOD_RESPONSE_PROMPT,
    DEMOGRAPHIC_EXTRACTION_PROMPT,  # kept in case you use it elsewhere
)

LOG_FILE = os.path.join(ROOT, "chat_log.txt")

# ------------------------------------------------------------------------------------------
# OpenAI client helpers (lazy; never read secrets at import-time to avoid Streamlit errors)
# ------------------------------------------------------------------------------------------

def _get_openai_api_key() -> Optional[str]:
    # 1) environment variable
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # 2) streamlit secrets (various layouts)
    try:
        import streamlit as st  # local import to avoid hard dependency during import
        s = st.secrets
        for path in [
            ("openai_api_key",),
            ("OPENAI_API_KEY",),
            ("openai", "api_key"),
        ]:
            try:
                v = s
                for p in path:
                    v = v[p]
                if v:
                    return str(v)
            except Exception:
                pass
    except Exception:
        pass

    return None


def _get_openai_client():
    """
    Returns a client object or None.
    Supports:
      - New SDK: from openai import OpenAI → client.chat.completions.create(...)
      - Legacy SDK: import openai → openai.ChatCompletion.create(...)
    """
    api_key = _get_openai_api_key()
    if not api_key:
        return None

    # Try new SDK first
    try:
        from openai import OpenAI  # type: ignore
        return OpenAI(api_key=api_key)
    except Exception:
        pass

    # Fallback to legacy SDK
    try:
        import openai  # type: ignore
        openai.api_key = api_key
        return openai
    except Exception:
        return None


def _chat_completion(messages: List[Dict[str, Any]], model: str = "gpt-4o-mini", temperature: float = 0.5) -> Optional[str]:
    """
    Calls Chat Completions API if available, else returns None.
    Works with both new and legacy SDKs.
    """
    client = _get_openai_client()
    if client is None:
        return None

    # Prefer new SDK style
    try:
        # duck-typing: new client has .chat.completions.create
        chat = getattr(client, "chat", None)
        if chat and hasattr(chat, "completions") and hasattr(chat.completions, "create"):
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
    except Exception:
        pass

    # Legacy SDK style
    try:
        if hasattr(client, "ChatCompletion"):
            resp = client.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return resp["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return None


# -----------------------
# Utility: file logging
# -----------------------

def log_to_file(content: str) -> None:
    try:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {content}\n")
    except Exception:
        # Never crash the app for logging issues
        pass


# -----------------------
# Public API (kept names)
# -----------------------

def get_chat_response(user_prompt: str, messages: Optional[List[Dict[str, str]]] = None, model: str = "gpt-4o-mini") -> str:
    """
    Wrapper around Chat Completions. If no API key is configured,
    returns a simple, safe fallback string.
    """
    chat_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    if messages:
        chat_messages.extend(messages)
    else:
        chat_messages.append({"role": "user", "content": user_prompt})

    out = _chat_completion(chat_messages, model=model, temperature=0.7)
    if out is not None:
        log_to_file(f"User prompt: {user_prompt[:80]}... | Reply: {out[:120]}...")
        return out

    # Fallback when GPT is unavailable
    return (
        "Thanks for sharing. I’m here to reflect and support you. "
        "While I can’t access AI generation right now, we can still walk through this together."
    )


# ------- Extractors (GPT if available, otherwise rule-based) -------

# Simple heuristics for name, age, gender
_NAME_RE = re.compile(r"\b(?:i'?m|i am|my name is|call me)\s+([A-Za-z][A-Za-z\-\']{1,30})\b", re.I)

def extract_name_from_input(user_input: str) -> Optional[str]:
    if not user_input:
        return None

    # Try GPT
    prompt = f"""
You are a helpful assistant. Extract a human name from the following message.
If no name is clearly mentioned, reply only with "None".

Message: "{user_input}"
Name:
"""
    gpt = _chat_completion([{"role": "user", "content": prompt}], model="gpt-4o-mini", temperature=0.2)
    if gpt:
        name = gpt.strip()
        return name if name.lower() != "none" else None

    # Fallback regex
    m = _NAME_RE.search(user_input.strip())
    if m:
        return m.group(1).strip().title()
    toks = re.findall(r"[A-Za-z][A-Za-z\-\']{1,30}", user_input)
    if len(toks) == 1:
        return toks[0].title()
    return None


def extract_age(user_input: str) -> Optional[int]:
    if not user_input:
        return None
    if user_input.isdigit():
        age = int(user_input)
        return age if 5 <= age <= 110 else None

    # GPT attempt
    prompt = f'Extract an age (as a number) from this message: "{user_input}". If none, respond "none".'
    gpt = _chat_completion([{"role": "user", "content": prompt}], model="gpt-4o-mini", temperature=0.2)
    if gpt:
        val = gpt.strip().lower()
        if val.isdigit():
            n = int(val)
            return n if 5 <= n <= 110 else None

    # Fallback parse
    nums = re.findall(r"\b(\d{1,3})\b", user_input)
    for n in nums:
        try:
            v = int(n)
            if 5 <= v <= 110:
                return v
        except ValueError:
            pass
    return None


_GENDER_MAP = {
    "male": "male",
    "man": "male",
    "m": "male",
    "female": "female",
    "woman": "female",
    "f": "female",
    "non-binary": "other",
    "nonbinary": "other",
    "enby": "other",
    "nb": "other",
    "agender": "other",
    "genderqueer": "other",
    "genderfluid": "other",
    "gender fluid": "other",
    "trans": "other",
    "transgender": "other",
    "other": "other",
    "prefer not to say": "other",
}

def extract_gender(user_input: str) -> Optional[str]:
    if not user_input:
        return None

    # GPT attempt
    prompt = f'Extract gender from this message: "{user_input}". Reply with "male", "female", "other", or "none".'
    gpt = _chat_completion([{"role": "user", "content": prompt}], model="gpt-4o-mini", temperature=0.2)
    if gpt:
        val = gpt.strip().lower()
        if val in ["male", "female", "other"]:
            return val
        return None

    # Fallback mapping
    t = user_input.strip().lower()
    for k, v in _GENDER_MAP.items():
        if k in t or t == k:
            return v
    # very short single token like 'm'/'f'
    toks = re.findall(r"[A-Za-z\-]+", t)
    if len(toks) == 1:
        return _GENDER_MAP.get(toks[0])
    return None


# ------- Screening summaries -------

def summarize_phq9(phq_scores):
    total = sum(phq_scores)
    prompt = PHQ9_SUMMARY_PROMPT.format(phq_total=total, phq_scores=phq_scores)
    out = get_chat_response(prompt)
    return total, out


def summarize_gad7(gad_scores):
    total = sum(gad_scores)
    prompt = GAD7_SUMMARY_PROMPT.format(gad_total=total, gad_scores=gad_scores)
    out = get_chat_response(prompt)
    return total, out


def summarize_results(phq_total: int, phq_level: str, gad_total: int, gad_level: str, mood_text: str = "") -> str:
    # Prefer your FINAL_SUMMARY_PROMPT if you want; keeping your original logic w/ inline prompt:
    prompt = (
        "The user completed a PHQ-9 and GAD-7 mental health screening.\n\n"
        "Mood Reflection:\n"
        f"{mood_text.strip()}\n\n"
        f"PHQ-9 score: {phq_total} ({phq_level})\n"
        f"GAD-7 score: {gad_total} ({gad_level})\n\n"
        "Please write a warm, supportive, and human-sounding summary (2–3 sentences) that:\n"
        "- Acknowledges their mood reflection\n"
        "- Gently names the depression and anxiety levels\n"
        "- Encourages care without sounding clinical or alarmist"
    )
    return get_chat_response(prompt)


# ------- Safety + Mood -------

def safety_check(user_input: str) -> bool:
    # quick conservative local check first
    t = (user_input or "").lower()
    red_flags = [
        "suicide", "suicidal", "end my life", "kill myself", "die", "want to die",
        "self-harm", "self harm", "hurt myself", "overdose", "jump off", "hang myself",
    ]
    if any(p in t for p in red_flags):
        return True

    # your prompt-based check
    try:
        prompt = SAFETY_CHECK_PROMPT.format(user_input=user_input)
    except Exception:
        prompt = f"Classify if this indicates imminent self-harm risk. Reply 'CRISIS' or 'SAFE'.\n\n{user_input}"

    resp = get_chat_response(prompt)
    return resp.strip().upper().startswith("CRISIS")


def respond_to_feelings(user_input: str, name: str) -> str:
    try:
        prompt = MOOD_RESPONSE_PROMPT.format(user_input=user_input, name=name or "there")
    except Exception:
        prompt = (
            f"You are Elli, a warm, concise, supportive assistant. "
            f"User ({name or 'there'}) wrote:\n{user_input}\n\n"
            f"Write 2–3 sentences reflecting one or two specifics and end with a gentle, open question."
        )
    return get_chat_response(prompt)
