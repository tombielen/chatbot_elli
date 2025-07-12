import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from collections import Counter
import nltk
import os

nltk.download('stopwords')
from nltk.corpus import stopwords

df = pd.read_csv("data/Chatbot_Study_Data_Cleaned.csv")
df = df[df["Dropout_status"] == 0].copy()
df["Version"] = df["Version"].str.strip().str.capitalize()

df = df[df["Feedback"].notna() & df["Feedback"].str.strip().ne("")].copy()

df["Cleaned_feedback"] = (
    df["Feedback"]
    .str.lower()
    .str.replace(r"[^\w\s]", "", regex=True)
    .str.strip()
)


os.makedirs("outputs/qualitative", exist_ok=True)
df.to_csv("outputs/qualitative/cleaned_feedback.csv", index=False)
print("✅ Cleaned feedback saved to: outputs/qualitative/cleaned_feedback.csv")

stopwords_custom = set(STOPWORDS).union(stopwords.words("english"))
stopwords_custom.update(["elli", "chatbot", "static", "feel", "felt"])  

all_text = " ".join(df["Cleaned_feedback"])
wordcloud = WordCloud(
    width=1000, height=500,
    background_color="white",
    stopwords=stopwords_custom,
    collocations=True
).generate(all_text)

os.makedirs("figures", exist_ok=True)
plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("Most Common Words in Participant Feedback", fontsize=16)
plt.tight_layout()
plt.savefig("figures/wordcloud_feedback.png", dpi=300)
plt.close()
print("📊 Word cloud saved to: figures/wordcloud_feedback.png")

def get_top_words(text_series):
    words = " ".join(text_series).split()
    words = [w for w in words if w not in stopwords_custom]
    return Counter(words).most_common(20)

elli_words = get_top_words(df[df["Version"] == "Elli"]["Cleaned_feedback"])
static_words = get_top_words(df[df["Version"] == "Static"]["Cleaned_feedback"])

pd.DataFrame(elli_words, columns=["Word", "Frequency"]).to_csv("outputs/qualitative/elli_word_freq.csv", index=False)
pd.DataFrame(static_words, columns=["Word", "Frequency"]).to_csv("outputs/qualitative/static_word_freq.csv", index=False)

