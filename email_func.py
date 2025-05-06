import nltk

import enchant
import spacy
import re
import numpy as np
import string
from summary_scoring import calculate_grammar_score
from essay_scoring import calculate_vocab_range_score_eassy,calculate_form_score_essay

nltk.data.path.append('nltk_data/')

nlp = spacy.load("en_core_web_sm")





def calculate_spelling_score_mail(essay):



    dictionary = enchant.Dict("en_US")


    words = essay.split()


    misspelled = [word for word in words if not (dictionary.check(word.strip(string.punctuation)) or word.strip(string.punctuation) == '')]
    misspelled = [item for item in misspelled if item != "•"]
    print(misspelled)
    misspelled_words=len(misspelled)
    print("Number of mispelled words: ",misspelled_words)
    if misspelled_words==0:
       score=2.0
    elif misspelled_words==1:
       print("if misspelled words are 1")
       score=1.0
    else:
        score=0.0
    return score




def email_convention_score_func(email):
    score = 0
    
    # Check if email starts with "Dear"
    if email.startswith("Dear"):
        score += 0.5
    
    # Check if email ends with a proper salutation
    if re.search(r'\b(Sincerely|Best regards|Yours sincerely|Regards)\b', email):
        score += 0.5
    
    # Check if email contains a clear subject line
    if "Subject:" in email:
        score += 0.5
    
    # Check if email contains a closing signature
    if re.search(r'\b(Thanks|Thank you|Best|Sincerely)\b', email):
        score += 0.5
    
    # Check if email contains proper greeting
    if re.search(r'\b(Hello|Hi|Hey)\b', email):
        score += 0.5
    
    # Check if email contains proper closing statement
    if re.search(r'\b(Sincerely|Best regards|Yours sincerely|Regards)\b', email):
        score += 0.5
    
    # Check if email contains polite language
    if re.search(r'\b(thank you|please)\b', email, re.IGNORECASE):
        score += 0.5
    
    # Check if email contains attachment
    if "Attachment" in email or "attached" in email:
        score += 0.5
    
    # Check if email contains urgency keywords
    if re.search(r'\b(urgent|asap|quick|immediately)\b', email, re.IGNORECASE):
        score -= 0.5
    
    # Check if email contains proper formatting
    if re.search(r'\n\n', email):
        score += 0.5
    print(score)
    
    # Ensure the score does not exceed 2
    return min(score, 2)


def preprocess_text(text):
    # Tokenize the text and remove stop words
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]

    # Lemmatize the tokens
    lemmatized_tokens = [token.lemma_ for token in nlp(" ".join(tokens))]

    # Join the lemmatized tokens back into a string
    preprocessed_text = ' '.join(lemmatized_tokens)

    return preprocessed_text


def calculate_content_score_mail(essay, question):
    # Preprocess essay and question
    preprocessed_essay = preprocess_text(essay)
    preprocessed_question = preprocess_text(question)

    # Calculate similarity between the preprocessed essay and question
    essay_embedding = nlp(preprocessed_essay).vector
    question_embedding = nlp(preprocessed_question).vector

    # Calculate cosine similarity between the essay and the question embeddings
    similarity_score = essay_embedding.dot(question_embedding) / (np.linalg.norm(essay_embedding) * np.linalg.norm(question_embedding))
    print("Similarity score: ", similarity_score)
       # Threshold for very dissimilar passages
    dissimilarity_threshold = 0.52
    if similarity_score<dissimilarity_threshold:
      return 0
 
    scaled_score = similarity_score * 3  # Scale to fit within 0 to 3 range
    if scaled_score==0:
       updated_score=0
    elif scaled_score > 0 and  scaled_score <= 0.5:
       updated_score=0.5
    elif scaled_score > 0.5 and  scaled_score <= 1.0:
       updated_score=1.0
    elif scaled_score > 1.0 and  scaled_score <= 1.5:
       updated_score=1.5
    elif scaled_score > 1.5 and  scaled_score <= 2.0:
       updated_score=2.0
    elif scaled_score > 2.0 and  scaled_score <= 2.5:
       updated_score=2.5
    else:
      updated_score=3.0

    return updated_score

def score_email_organization(email):
    score = 0
    
    # Check for subject line
    if re.search(r"Subject:", email):
        score += 0.5
    
    # Check for greeting and closing
    if re.search(r"Dear .*?,", email) and re.search(r"Best,", email):
        score += 0.5
    
    # Check for main content
    if re.search(r"Dear .*?,\n\n(.|\n)*\nBest,", email):
        score += 1
    
    # Check for additional criteria
    if re.search(r"\bI hope\b", email):
        score += 0.25
    if re.search(r"\bI'm suggesting\b", email):
        score += 0.25
    if re.search(r"\bBy choosing\b", email):
        score += 0.25
    if re.search(r"\bThis piece\b", email):
        score += 0.25
    if re.search(r"\bcould inspire\b", email):
        score += 0.25
    
    # Normalize score to range from 0 to 2

    
    return score


def score_email(essay,question,accent):
    content_score = calculate_content_score_mail(essay,question)
    grammar_score = calculate_grammar_score(essay)
    vocab_range_score = calculate_vocab_range_score_eassy(essay)
    spelling_score = calculate_spelling_score_mail(essay)
    form_score = calculate_form_score_essay(essay)
    email_convention_score = email_convention_score_func(essay)
    org_score = score_email_organization(essay)


    total_score = content_score + grammar_score + vocab_range_score + spelling_score + form_score + email_convention_score + org_score
    total_score=round(total_score,1)
    updated_score=round(total_score * 4) / 4


    return content_score, grammar_score, vocab_range_score, spelling_score, form_score, email_convention_score, org_score, updated_score

