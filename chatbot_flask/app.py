from flask import Flask, render_template, request

app = Flask(__name__)

# Initialize an in-memory list to store chat history
chat_history = []

# Load spaCy's English model
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Initialize the spell checker
from spellchecker import SpellChecker
spell = SpellChecker()

# Import necessary modules
import pandas as pd
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

FILE_PATH = "documents/scraped_data1.csv"

def split_into_sentences(text):
    if isinstance(text, float):
        text = str(text) if not pd.isna(text) else ""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences


def lemmatize_sentence(sentence):
    doc = nlp(sentence.lower())
    lemmatized_words = [token.lemma_ for token in doc if not token.is_punct and not token.is_space]
    return ' '.join(lemmatized_words)

def correct_spelling(text):
    words = text.split()
    corrected_words = [spell.correction(word) for word in words]
    return ' '.join(corrected_words)

def find_relevant_sentences(query, sentences, lemmatized_sentences):
    lemmatized_query = lemmatize_sentence(query)

    # Fuzzy matching
    scores = [fuzz.partial_ratio(lemmatized_query, ls) for ls in lemmatized_sentences]
    best_matches = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    threshold = 90
    relevant_sentences = [sentences[i] for i, score in best_matches if score >= threshold]
    
    if not relevant_sentences:
        # Use TF-IDF and cosine similarity
        vectorizer = TfidfVectorizer().fit(sentences + [lemmatized_query])
        vectors = vectorizer.transform(sentences + [lemmatized_query])
        cosine_similarities = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
        
        best_idx = cosine_similarities.argmax()
        if cosine_similarities[best_idx] > 0.15:
            relevant_sentences = [sentences[best_idx]]
    
    return relevant_sentences

def process_query(query):
    query = query.lower().strip()
    
    # Predefined responses for common questions
    greetings = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hi there! How can I help you?",
        "good morning": "Good morning! What can I do for you today?",
        "good afternoon": "Good afternoon! How can I assist you?",
        "good evening": "Good evening! How can I help you?",
        "how are you": "I'm just a bot, but I'm here to help you!",
        "what is your name": "I'm a chatbot designed to assist you with queries related to the Department of Justice."
    }
    
    # Check for predefined responses
    if query in greetings:
        return greetings[query]
    
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)

        if 'text' not in df.columns:
            return "The CSV file must contain a 'text' column."

        sentences = []
        lemmatized_sentences = []

        for doc in df['text']:
            for sentence in split_into_sentences(doc):
                sentences.append(sentence.strip())
                lemmatized_sentences.append(lemmatize_sentence(sentence.strip()))

        corrected_query = correct_spelling(query)
        relevant_sentences = find_relevant_sentences(corrected_query, sentences, lemmatized_sentences)

        if relevant_sentences:
            return " ".join(relevant_sentences)
        else:
            return "No relevant results found."
    else:
        return f"File not found: {FILE_PATH}"

@app.route("/", methods=["GET", "POST"])
def index():
    global chat_history

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            response = process_query(query)
            chat_history.append({"type": "user-msg", "text": query})
            chat_history.append({"type": "bot-msg", "text": response})

    return render_template("chat.html", chat_history=chat_history)

if __name__ == "__main__":
    app.run(debug=True)
