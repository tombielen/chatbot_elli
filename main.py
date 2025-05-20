import time

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

def ask_consent():
    print("\nHi, I'm Elli, your mental health check-in assistant.")
    time.sleep(1)
    print("\nBefore we begin, please note:")
    print("- This is not a medical tool.")
    print("- Your responses are anonymous.")
    print("- You can stop at any time.")
    consent = input("\nDo you agree to continue? (yes/no): ")
    return consent.lower() == "yes"

def ask_questionnaire(questions, label):
    print(f"\nLet's start the {label} questionnaire.")
    scores = []
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. Over the last two weeks, how often have you been bothered by the following?")
        print(q)
        print("0 = Not at all | 1 = Several days | 2 = More than half the days | 3 = Nearly every day")
        while True:
            try:
                score = int(input("Your answer (0–3): "))
                if score in [0, 1, 2, 3]:
                    break
                else:
                    print("Invalid input. Please enter 0, 1, 2, or 3.")
            except ValueError:
                print("Please enter a number.")
        scores.append(score)
    return scores

def summarize_results(phq_scores, gad_scores):
    phq_total = sum(phq_scores)
    gad_total = sum(gad_scores)

    print("\n Thank you for completing the questionnaires.")
    print(f"\nYour PHQ-9 total score: {phq_total}/27")
    print(f"Your GAD-7 total score: {gad_total}/21")

    def interpret(score, scale):
        if scale == "phq":
            if score <= 4: return "Minimal depression"
            elif score <= 9: return "Mild depression"
            elif score <= 14: return "Moderate depression"
            elif score <= 19: return "Moderately severe depression"
            else: return "Severe depression"
        if scale == "gad":
            if score <= 4: return "Minimal anxiety"
            elif score <= 9: return "Mild anxiety"
            elif score <= 14: return "Moderate anxiety"
            else: return "Severe anxiety"

    print(f"Depression Level: {interpret(phq_total, 'phq')}")
    print(f"Anxiety Level: {interpret(gad_total, 'gad')}")

def main():
    if not ask_consent():
        print("No worries. Take care of yourself.")
        return

    phq_scores = ask_questionnaire(PHQ_9_QUESTIONS, "PHQ-9")
    gad_scores = ask_questionnaire(GAD_7_QUESTIONS, "GAD-7")

    summarize_results(phq_scores, gad_scores)

if __name__ == "__main__":
    main()