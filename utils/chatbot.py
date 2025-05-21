import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import openai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gpt_prompts import (
    PHQ9_SUMMARY_PROMPT,
    GAD7_SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    SAFETY_CHECK_PROMPT,
    SYSTEM_INSTRUCTION
)


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

LOG_FILE = "chat_log.txt"

def log_to_file(content):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {content}\n")


def get_chat_response(prompt, messages=None, model="gpt-4"):
    chat_messages = [{"role": "system", "content": prompt}]
    if messages:
        chat_messages.extend(messages)

    response = openai.ChatCompletion.create(
        model=model,
        messages=chat_messages,
        temperature=0.7
    )
    reply = response.choices[0].message["content"].strip()
    log_to_file(f"Prompt: {prompt[:50]}... | Reply: {reply}")
    return reply


def summarize_phq9(phq_scores):
    total = sum(phq_scores)
    response = get_chat_response(
        PHQ9_SUMMARY_PROMPT.format(phq_total=total, phq_scores=phq_scores)
    )
    return total, response


def summarize_gad7(gad_scores):
    total = sum(gad_scores)
    response = get_chat_response(
        GAD7_SUMMARY_PROMPT.format(gad_total=total, gad_scores=gad_scores)
    )
    return total, response


def summarize_results(phq_total, phq_level, gad_total, gad_level):
    summary = get_chat_response(
        FINAL_SUMMARY_PROMPT.format(
            phq_total=phq_total,
            phq_interpretation=phq_level,
            gad_total=gad_total,
            gad_interpretation=gad_level
        )
    )
    return summary


def safety_check(user_input):
    result = get_chat_response(
        SAFETY_CHECK_PROMPT.format(user_input=user_input)
    )
    return result.strip().upper() == "CRISIS"