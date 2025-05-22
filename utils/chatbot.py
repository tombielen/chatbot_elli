import os
import sys
from datetime import datetime
from dotenv import load_dotenv 
from openai import OpenAI

load_dotenv() 
print("Current working directory:", os.getcwd())
print("API KEY from .env:", os.getenv("OPENAI_API_KEY"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gpt_prompts import (
    PHQ9_SUMMARY_PROMPT,
    GAD7_SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    SAFETY_CHECK_PROMPT,
    SYSTEM_INSTRUCTION,
    MOOD_RESPONSE_PROMPT,
    DEMOGRAPHIC_EXTRACTION_PROMPT
)




LOG_FILE = "chat_log.txt"

NAME_VALIDATION_PROMPT = """
A user was asked for their name or nickname and replied with:
"{user_input}"

Is this likely a name/nickname? Respond only with "YES" or "NO".
"""

def extract_name_from_input(user_input):
    prompt = f"""
    You are a helpful assistant. Extract a human name from the following message.
    If no name is clearly mentioned, reply only with "None".

    Message: "{user_input}"
    Name:
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    name = response.choices[0].message.content.strip()
    return name if name.lower() != "none" else None

def log_to_file(content):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {content}\n")

def get_chat_response(user_prompt, messages=None, model="gpt-4"):
    chat_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    
    if messages:
        chat_messages.extend(messages)
    else:
        chat_messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=chat_messages,
        temperature=0.7
    )
    reply = response.choices[0].message.content.strip()
    log_to_file(f"User prompt: {user_prompt[:50]}... | Reply: {reply}")
    return reply

def summarize_phq9(phq_scores):
    total = sum(phq_scores)
    prompt = PHQ9_SUMMARY_PROMPT.format(phq_total=total, phq_scores=phq_scores)
    response = get_chat_response(prompt)
    return total, response

def summarize_gad7(gad_scores):
    total = sum(gad_scores)
    prompt = GAD7_SUMMARY_PROMPT.format(gad_total=total, gad_scores=gad_scores)
    response = get_chat_response(prompt)
    return total, response

def summarize_results(phq_total, phq_level, gad_total, gad_level, mood_text=""):
    prompt = (
        "The user completed a PHQ-9 and GAD-7 mental health screening.\n\n"
        "Mood Reflection:\n"
        f"{mood_text.strip()}\n\n"
        "PHQ-9 score: {phq_total} ({phq_level})\n"
        "GAD-7 score: {gad_total} ({gad_level})\n\n"
        "Please write a warm, supportive, and human-sounding summary (2–3 sentences) that:\n"
        "- Acknowledges their mood reflection\n"
        "- Gently names the depression and anxiety levels\n"
        "- Encourages care without sounding clinical or alarmist"
    ).format(
        phq_total=phq_total,
        phq_level=phq_level,
        gad_total=gad_total,
        gad_level=gad_level
    )
    return get_chat_response(prompt)


def safety_check(user_input):
    prompt = SAFETY_CHECK_PROMPT.format(user_input=user_input)
    response = get_chat_response(prompt)
    return response.strip().upper() == "CRISIS"

def respond_to_feelings(user_input, name):
    prompt = MOOD_RESPONSE_PROMPT.format(user_input=user_input, name=name)
    return get_chat_response(prompt)

def extract_age(user_input):
    if user_input.isdigit():
        return int(user_input)

    prompt = f"""
    Extract an age (as a number) from this message: "{user_input}"
    If there's no age, respond with "none".
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    value = response.choices[0].message.content.strip().lower()
    return int(value) if value.isdigit() else None

def extract_gender(user_input):
    prompt = f"""
    Extract gender from this message: "{user_input}"
    Reply with "male", "female", "other", or "none".
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    value = response.choices[0].message.content.strip().lower()
    if value in ["male", "female", "other"]:
        return value
    return None

def extract_history(user_input):
    prompt = f"""
    Does this message indicate any prior mental health support or history?
    "{user_input}"
    Reply with "has history", "no history", or "none".
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    value = response.choices[0].message.content.strip().lower()
    if value in ["has history", "no history"]:
        return value
    return None
