import string
from collections import Counter
import enchant
import re


def writedictationscoring(correct_answer, user_response, score):

    # Helper function to remove final punctuation
    def remove_final_punctuation(sentence):
        if sentence and sentence[-1] in string.punctuation:
            return sentence[:-1]
        return sentence
    
    # Get the words along with their start indices
    def split_with_indices(sentence):
        words = sentence.split()
        indices = []
        start = 0
        for word in words:
            start = sentence.find(word, start)
            end = start + len(word)
            indices.append((start, end))
            start = end  # Move to the next word
        return words, indices
    
    # Remove final punctuation from both correct answer and user response
    correct_answer_no_punc = remove_final_punctuation(correct_answer)
    user_response_no_punc = remove_final_punctuation(user_response)
    
    # Split with indices
    correct_words, correct_indices = split_with_indices(correct_answer_no_punc)
    user_words, user_indices = split_with_indices(user_response_no_punc)
    
    # Normalize word cases for consistent comparisons
    correct_words_lower = [word.lower() for word in correct_words]
    user_words_lower = [word.lower() for word in user_words]
    
    # Check if the first word is capitalized
    if len(user_words) > 0 and not user_words[0][0].isupper():
        score -= 0.5
    
    # Find the indices of matching words in user response
    matching_indices = [
        user_indices[i] for i in range(len(user_words_lower)) if user_words_lower[i] in correct_words_lower
    ]
    
    # Find the matching words in user response that are in the correct answer
    matched_words = [
        user_words[i] for i in range(len(user_words_lower)) if user_words_lower[i] in correct_words_lower
    ]
    
    # Find the indices of unmatched words in the user response
    incorrect_indices = []
    incorrect_words = []
    user_word_counts = Counter(user_words_lower)

    for i, word in enumerate(user_words_lower[::-1]):
        if word in correct_words_lower and user_word_counts[word] > correct_words_lower.count(word):
            last_index = len(user_words_lower) - 1 - i
            incorrect_indices.append(user_indices[last_index])
            incorrect_words.append(user_words[last_index])
            user_word_counts[word] -= 1
    
    # Find the words in the user response that do not match any in correct answer
    # These are the ones that didn't match and were not already accounted for
    for i in range(len(user_words_lower)):
        if user_words_lower[i] not in correct_words_lower and user_indices[i] not in incorrect_indices:
            incorrect_indices.append(user_indices[i])
            incorrect_words.append(user_words[i])

    # Find words from the correct answer that aren't in the user response (missed words)
    # Create frequency counters for correct and user words
    correct_word_counts = Counter(correct_words_lower)
    user_word_counts = Counter(user_words_lower)
    
    # Find words from the correct answer that aren't in the user response
    missed_words = []
    missed_word_indices = []
    for i, word in enumerate(correct_word_counts):
        correct_count = correct_word_counts[word]
        user_count = user_word_counts.get(word, 0)
        
        if user_count < correct_count:
            missing_count = correct_count - user_count
            # Add the word to missed_words the number of times it is missing
            missed_words.extend([word] * (correct_count - user_count))
            missed_word_indices.extend([correct_indices[i]] * missing_count)
    
    # Find words from the user response that are in excess compared to correct answer
    excess_words = []
    excess_word_indices = []
    for i, word in enumerate(user_words_lower):
        user_count = user_word_counts[word]
        correct_count = correct_word_counts.get(word, 0)
        
        if user_count > correct_count:
            excess_count = user_count - correct_count
            # Add the excess word to excess_words the number of times it exceeds
            excess_words.extend([user_words[i]] * (user_count - correct_count))
            excess_word_indices.extend([user_indices[i]] * excess_count)
    
    # Count the number of missed words and deduct 1 point per missed word
    score -= len(missed_words)
    
    # Remove the matching indices that are also in incorrect indices
    for index in incorrect_indices:
        if index in matching_indices:
            matching_indices.remove(index)
    
    # Deduct 0.5 mark if there's no punctuation at the end
    if correct_answer.endswith(('.', '!', '?')):
        if not user_response or user_response[-1] not in string.punctuation:
            score -= 0.5
    
    score = max(score, 0)
    
    # Return score, matching indices, matched words, incorrect indices, incorrect words, missed words, missed word indices,
    # excess words, and excess word indices
    return score, matching_indices, matched_words, incorrect_indices, incorrect_words, missed_words, missed_word_indices



def calculate_spelling_score(summary, accent, grammatical_indices):
    if accent == "en-us":
        dictionary = enchant.Dict("en_US")
    elif accent == "en-uk":
        dictionary = enchant.Dict("en_GB")

    words = re.finditer(r'\b\w+\b', summary)  # Using re.finditer to get word indices
    misspelled_corrected = {}
    misspelled_words = 0
    misspelled_word_indices = []  # Initialize list for misspelled word indices

    for match in words:
        start_index = match.start()
        end_index = match.end()
        word = summary[start_index:end_index]
        if not dictionary.check(word):
            suggestions = dictionary.suggest(word)
            if suggestions:
                corrected_word = suggestions[0]  # Choosing the first suggestion as the corrected word
                if len(word) > 2 and word.replace(" ", "") == corrected_word.replace(" ", ""):
                    # If the original word and suggested word without spaces are the same,
                    # it's likely a compound word that was split incorrectly
                    continue
                # Check if the starting or ending index of the misspelled word matches with any grammatical index
                if any(start_index == g_start or end_index == g_end for g_start, g_end in grammatical_indices):
                    continue  # Skip counting the misspelled word and excluding it from the corrected words
                if word.lower() in ["multitaskers", "intentionality", "unfollowing", "underserved", "quo"]:
                    continue  # Skip the above array words
                misspelled_corrected[word] = corrected_word
                misspelled_words += 1
                misspelled_word_indices.append((start_index, end_index))  # Store misspelled word indices

    print("Number of misspelled words:", misspelled_words)

    if misspelled_words == 0:
        score = 2.0
    elif misspelled_words == 1:
        score = 1.0
    else:
        score = 0.0

    return score, misspelled_corrected, misspelled_word_indices
 