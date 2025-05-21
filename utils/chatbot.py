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
    MOOD_RESPONSE_PROMPT
)

LOG_FILE = "chat_log.txt"

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

def summarize_results(phq_total, phq_level, gad_total, gad_level):
    prompt = FINAL_SUMMARY_PROMPT.format(
        phq_total=phq_total,
        phq_interpretation=phq_level,
        gad_total=gad_total,
        gad_interpretation=gad_level
    )
    return get_chat_response(prompt)

def safety_check(user_input):
    prompt = SAFETY_CHECK_PROMPT.format(user_input=user_input)
    response = get_chat_response(prompt)
    return response.strip().upper() == "CRISIS"

def respond_to_feelings(user_input, name):
    prompt = MOOD_RESPONSE_PROMPT.format(user_input=user_input, name=name)
    return get_chat_response(prompt)
