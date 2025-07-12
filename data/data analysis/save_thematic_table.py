import pandas as pd
import os
data = {
    "Theme": [
        "Perceived lack of humanity",
        "Authenticity concern in empathy simulation",
        "Emotional awkwardness or discomfort",
        "Transactional trust and clarity",
        "Usability and credibility",
        "Feeling heard without social pressure"
    ],
    "Condition": [
        "Elli",
        "Elli",
        "Elli",
        "Static",
        "Static",
        "Static"
    ],
    "Sample Words": [
        "robotic, unnatural, talk, human",
        "therapy, push back, not for me",
        "bad, not helpful, toxic positivity",
        "good, nice, questionnaire, reflect",
        "scale, rating, psychology, options",
        "cool, asked, free, someone"
    ],
    "Representative Quote": [
        "I think Elli sounds too ‘robotic’. It could be more ‘human’.",
        "When talking about deep subjects I need to be talking to someone who can actually push back.",
        "These questions can feel pretty bad… Elli should ask further questions about how I feel.",
        "I thought the questions themselves were very good and it was nice to reflect on these things.",
        "The use of rating scales used in psychology lends it credibility.",
        "It was pretty cool to be asked these type of questions... it’s good to be free with someone at least."
    ]
}

df = pd.DataFrame(data)

output_path = "outputs/qualitative"
os.makedirs(output_path, exist_ok=True)
file_path = os.path.join(output_path, "thematic_summary.csv")
df.to_csv(file_path, index=False)
