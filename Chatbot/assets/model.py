import streamlit as st
import os
import pandas as pd
import re
import spacy
from spellchecker import SpellChecker
import speech_recognition as sr

# Load spaCy's English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If the model is not found, download it
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "spacy",
                   "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Initialize the spell checker
spell = SpellChecker()

# Initialize the speech recognizer
recognizer = sr.Recognizer()


def add_vertical_space(spaces=1):
    for _ in range(spaces):
        st.sidebar.markdown("---")


def split_into_sentences(text):
    # Use spaCy's sentence segmentation
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences


def lemmatize_sentence(sentence):
    doc = nlp(sentence.lower())
    lemmatized_words = [
        token.lemma_ for token in doc if not token.is_punct and not token.is_space]
    return ' '.join(lemmatized_words)


def correct_spelling(text):
    words = text.split()
    corrected_words = [spell.correction(word) for word in words]
    return ' '.join(corrected_words)


def record_voice_input():
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        try:
            st.write("Processing voice input...")
            query = recognizer.recognize_google(audio)
            st.success(f"Recognized: {query}")
            return query
        except sr.UnknownValueError:
            st.error("Could not understand the audio")
        except sr.RequestError:
            st.error("Could not request results from the service")
    return ""


def main():
    st.set_page_config(page_title="CSV Search Chatbot with Voice Input")
    st.title("CSV Search Chatbot with Voice Input")

    st.sidebar.title("About")
    st.sidebar.markdown('''
        This chatbot uses keyword matching with lemmatization for document search and retrieval,
        can correct minor spelling mistakes, and accepts voice input.
    ''')

    TEMP_DIR = "temp"

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])

    add_vertical_space(1)
    st.sidebar.write('Made by [YourName](https://huggingface.co/YourName)')

    if uploaded_file is not None:
        file_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        st.write(f"Uploaded file: {uploaded_file.name}")
        st.write("Processing CSV file...")

        df = pd.read_csv(file_path)

        if 'text' not in df.columns:
            st.error("The CSV file must contain a 'text' column.")
            return

        # Tokenize documents into sentences using spaCy
        sentences = []
        lemmatized_sentences = []
        sentence_doc_mapping = []

        for i, doc in enumerate(df['text']):
            for sentence in split_into_sentences(doc):
                sentences.append(sentence.strip())
                lemmatized_sentences.append(
                    lemmatize_sentence(sentence.strip()))
                sentence_doc_mapping.append(i)

        st.write("Indexing completed.")

        query = ""  # Initialize query as an empty string

        query_option = st.radio("Choose input method:",
                                ("Text Input", "Voice Input"))

        if query_option == "Text Input":
            query = st.text_input("Enter your query:")
        else:
            if st.button("Record Voice Query"):
                query = record_voice_input()

        if query:  # Check if query is not an empty string
            with st.spinner("Processing your question..."):
                # Correct the spelling of the query
                corrected_query = correct_spelling(query)
                st.write(f"Corrected Query: {corrected_query}")

                # Lemmatize the corrected query
                lemmatized_query = lemmatize_sentence(corrected_query)

                # Find all sentences that contain the lemmatized query keyword
                relevant_sentences = [
                    sentences[i] for i, lemmatized_sentence in enumerate(lemmatized_sentences) if lemmatized_query in lemmatized_sentence
                ]

                if relevant_sentences:
                    st.write("Relevant Sentences:")
                    for sentence in relevant_sentences:
                        st.write("-", sentence)
                else:
                    st.write("No relevant results found.")

        # Clean up the uploaded file
        os.remove(file_path)



if __name__ == "__main__":
    main()
