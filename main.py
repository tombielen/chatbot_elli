# main.py

import time
import csv
import os
from utils.chatbot import summarize_results, safety_check

PHQ_9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading or watching TV?",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you’ve been moving around a lot more than usual?",
    "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way?"
]

GAD_7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge?",
    "Not being able to stop or control worrying?",
    "Worrying too much about different things?",
    "Trouble relaxing?",
    "Being so restless that it is hard to sit still?",
    "Becoming easily annoyed or irritable?",
    "Feeling afraid as if something awful might happen?"
]

SUS_QUESTIONS = [
    "I think I would like to use this chatbot frequently.",
    "I found the chatbot unnecessarily complex.",
    "I thought the chatbot was easy to use.",
    "I think I would need help to use this chatbot.",
    "I found the various functions well integrated.",
    "I thought there was too much inconsistency.",
    "I would imagine most people would learn to use it quickly.",
    "I found it very cumbersome to use.",
    "I felt very confident using the chatbot.",
    "I needed to learn a lot before I could get going."
]

def ask_likert(question, scale=(1, 5)):
    print(f"\n{question}")
    print(f"{scale[0]} = Strongly disagree | {scale[1]} = Strongly agree")
    while True:
        try:
            score = int(input(f"Your answer ({scale[0]}–{scale[1]}): "))
            if scale[0] <= score <= scale[1]:
                return score
            else:
                print("Invalid input. Try again.")
        except ValueError:
            print("Please enter a number.")

def ask_questionnaire(questions, label, scale=(0, 3)):
    print(f"\nStarting the {label} questionnaire.")
    scores = []
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. Over the last two weeks, how often have you been bothered by: {q}")
        print("0 = Not at all | 1 = Several days | 2 = More than half the days | 3 = Nearly every day")
        while True:
            try:
                score = int(input("Your answer (0–3): "))
                if scale[0] <= score <= scale[1]:
                    break
                else:
                    print("Invalid input. Please enter a number between 0 and 3.")
            except ValueError:
                print("Please enter a number.")
        scores.append(score)
    return scores

def interpret(score, scale):
    if scale == "phq":
        if score <= 4: return "Minimal depression"
        elif score <= 9: return "Mild depression"
        elif score <= 14: return "Moderate depression"
        elif score <= 19: return "Moderately severe depression"
        else: return "Severe depression"
    elif scale == "gad":
        if score <= 4: return "Minimal anxiety"
        elif score <= 9: return "Mild anxiety"
        elif score <= 14: return "Moderate anxiety"
        else: return "Severe anxiety"

def save_to_csv(data, filename="data/user_responses.csv"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def main():
    print("Hi, I’m Elli. I'm here to check in with you today 🌱")
    time.sleep(1)
    name = input("What’s your first name (or nickname) you'd like me to use?: ").strip() or "friend"

    print(f"\nNice to meet you, {name}. This isn’t therapy, but I hope it feels like a warm and thoughtful space.")
    time.sleep(1)
    mood = input("Before we dive in, how have things been for you lately? Just a sentence or two: ")

    if safety_check(mood):
        print("\nIt sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛")
        return

    print("\nA few questions to understand you better:")
    age = input("Age: ").strip()
    gender = input("Gender (or skip): ").strip()
    therapy = input("Have you done therapy before? (yes/no): ").strip().lower()

    phq_scores = ask_questionnaire(PHQ_9_QUESTIONS, "PHQ-9")
    gad_scores = ask_questionnaire(GAD_7_QUESTIONS, "GAD-7")

    phq_total = sum(phq_scores)
    gad_total = sum(gad_scores)
    phq_interp = interpret(phq_total, "phq")
    gad_interp = interpret(gad_total, "gad")

    summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
    print("\nThanks for completing those. Here's a short summary based on your scores:\n")
    print(summary)

    print("\nJust a few more questions about how you felt using Elli:")
    trust = ask_likert("I felt like I could trust Elli.")
    comfort = ask_likert("I felt comfortable interacting with Elli.")

    sus_scores = []
    print("\nSystem Usability Scale (SUS):")
    for q in SUS_QUESTIONS:
        score = ask_likert(q)
        sus_scores.append(score)

    sus_adjusted = []
    for i, score in enumerate(sus_scores):
        if i % 2 == 0:
            sus_adjusted.append(score - 1)
        else:
            sus_adjusted.append(5 - score)

    sus_score = sum(sus_adjusted) * 2.5

    reflection = input("\nAny thoughts or feedback you'd like to share about this experience?: ").strip()

    data = {
        "name": name,
        "age": age,
        "gender": gender,
        "therapy_history": therapy,
        "initial_mood": mood,
        "phq_total": phq_total,
        "phq_interp": phq_interp,
        "gad_total": gad_total,
        "gad_interp": gad_interp,
        "trust": trust,
        "comfort": comfort,
        "sus_raw": sus_score,
        "user_reflection": reflection
    }

    save_to_csv(data)
    print(f"\nThanks so much for checking in today, {name}. Wishing you care and calm. 🌼")

if __name__ == "__main__":
    main()
