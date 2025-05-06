import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
import spacy
import enchant
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from comments.summary_comments import set_summary_comments
from nltk.corpus import stopwords
from constants import WORD_LIST

nltk.data.path.append('nltk_data/')


def count_sentences(text):
    sentences = text.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]  # Remove empty strings and strip whitespace
    return len(sentences)


def count_multiple_spaces(text):
    print("in count spaces")
    pattern = r'\b(\w+)\s{2,}(\w+)\b'
    matches = re.finditer(pattern, text)
    print("matches:", matches)
    multispace_indices = []    
    results = []
    for match in matches:
        start_index = match.start()
        end_index = match.end()
        matched_text = match.group()
        results.append(matched_text)
        multispace_indices.append((start_index, end_index))
    return len(results), results, multispace_indices




def calculate_content_score_summary(passage, summary):
    
    updated_score = 2.0
    
    # Major aspects to ignore for minor aspects extraction
    # major_aspects = ["rosalind", "franklin", "pioneering", "scientist"]
    
    # Tokenize the passage into paragraphs and then into tokens
    paragraphs = passage.split("\n")  # Splitting the passage into paragraphs
    # print("PARAGRAPHS::",len(paragraphs))
    summary_tokens = nltk.word_tokenize(summary.lower())
    
    # Remove punctuation and stopwords from summary tokens
    summary_tokens = [token for token in summary_tokens if token.isalnum()]
    stop_words = set(stopwords.words('english'))
    summary_tokens = [token for token in summary_tokens if token not in stop_words]
    
    # List to store minor aspects from each paragraph
    paragraph_minor_aspects = []
    
    for paragraph in paragraphs:
        # Tokenize each paragraph
        paragraph_tokens = nltk.word_tokenize(paragraph.lower())
        paragraph_tokens = [token for token in paragraph_tokens if token.isalnum()]

        
        # Remove major aspects, stopwords, and numeric tokens
        # paragraph_tokens = [token for token in paragraph_tokens if token not in major_aspects]
        paragraph_tokens = [token for token in paragraph_tokens if token not in stop_words and not token.isdigit()]

        # print("Paragraph No")
        # print(paragraph_tokens)


        # Add unique minor aspects from each paragraph
        paragraph_minor_aspects.append(list(set(paragraph_tokens)))
    
    print("Paragraph Minor Aspects",paragraph_minor_aspects)


    print("Summary Tokens::", summary_tokens)
    # Count paragraphs where at least 2 minor aspects are in summary
    matching_paragraphs = 0

    for minor_aspects in paragraph_minor_aspects:
        matched_tokens = {token for token in summary_tokens if token in minor_aspects}
        if len(matched_tokens) >= 8:
            matching_paragraphs += 1
            print("Matching Tokens:", matched_tokens)  # Printing matched tokens

    

    print("Matching Paragraphs:",matching_paragraphs)
    # Deduction based on matching paragraphs
    if matching_paragraphs >= 3:
        print("I am here 1.")
        updated_score -= 0  # No deduction
    elif matching_paragraphs == 2:
        print("I am here 2.")
        updated_score -= 0.5  # Deduct if at least one paragraph doesn't have 2 matching minor aspects
    elif matching_paragraphs == 1:
        print("I am here 3.")
        updated_score -= 1
    elif matching_paragraphs == 0:
         # If no paragraphs match, check if at least 5 minor aspects are mentioned
        all_matched_tokens = [token for minor_aspect in paragraph_minor_aspects for token in summary_tokens if token in minor_aspect]
        unique_matched_tokens = set(all_matched_tokens)
        print("Unique Matched Tokens::", unique_matched_tokens)
        if len(unique_matched_tokens) >= 5:
            updated_score = 0.5 # Give 0.5 marks if 5 or more unique minor aspects are mentioned in total
        else:
            updated_score = 0.0 # Else 0 marks
    return updated_score


def calculate_spelling_score(summary, accent, grammatical_indices):
    if accent == "en-us":
        dictionary = enchant.Dict("en_US")
    elif accent == "en-uk":
        dictionary = enchant.Dict("en_GB")

    words = re.finditer(r'\b\w+\b', summary)  # Using re.finditer to get word indices
    misspelled_corrected = {}
    misspelled_words = 0
    misspelled_word_indices = []  # Initialize list for misspelled word indices

    # Check for all occurrences of the phrase "mind set"
    mind_set_matches = re.finditer(r'\bmind set\b', summary)
    for match in mind_set_matches:
        start_index = match.start()
        end_index = match.end()
        misspelled_corrected["mind set"] = "mindset"
        misspelled_words += 1
        misspelled_word_indices.append((start_index, end_index))

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
                if any(start_index == g_start or end_index == g_end for g_start, g_end, g_end1 in grammatical_indices):
                    continue  # Skip counting the misspelled word and excluding it from the corrected words
                if word.lower() in WORD_LIST:
                    continue  # Skip the word "multitaskers"
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


def calculate_grammar_score(summary, accent):
    print("Accent::", accent)
    # print(summary)
    grammatical_indices=[]
    count_double_space_occurance , grammar_mistakes, grammatical_indices = count_multiple_spaces(summary)
    print("count_double_space_occurance", count_double_space_occurance)
    print("Grammar Mistakes::", grammar_mistakes)
    nlp = spacy.load('en_core_web_sm')
    # print(nlp)
    doc = nlp(summary)
    # num_errors, spell_errors = calculate_spelling_score(summary, accent)
    # num_errors += count_double_space_occurance
    num_errors = count_double_space_occurance
    errors = []
    score = 2.0
    words_with_consonant_sound = ["Herb", "Honor", "Honest", "Unicorn", "European", "Unique", "Utensil", "Oven", "One", "Island", "Umbrella", "Urn", "Urge", "Urchin", "Awe", "Aye", "Aim", "Ark", "Ear", "Eagle", "Earn", "Earthen", "Early", "Earnest", "Eat", "Eel", "Eerie", "Eve", "Evil", "Eye", "Oil", "Oily", "Object", "Obstacle", "Occasion", "Occur", "Ocean", "Octave", "Octopus", "Ogle", "Ohm", "Ointment", "Omen", "Onset", "Onto", "Opera", "Operate", "Opportunity", "Opt", "Optic", "Oracle", "Oral", "Orbit", "Order", "Oregano", "Organ", "Orient", "Origin", "Ounce", "Our", "Oust", "Outlaw", "Ovation", "Over", "Overt", "Owl", "Owner", "Ox", "Oxen", "Oxygen"]
    vowels_not_starting_with_vowels = ['hour', 'heir', 'honor', 'honest', 'hymn', 'honorarium', 'honorific', 'houri', 'euro', 'eunuch', 'ewer']
    ed_ing_words = ["bed", "red", "shed", "wed", "led", "zed", "feed" ,"ced", "ded", "ged", "jed", "ned", "ped", "ted", "yed", "creed", "deed", "seed", "speed", "steed", "need", "sheed", "weed", "beed", "geed", "heed", "keed", "leed", "meed", "reed", "teed", "breed", "greed", "heed", "keed", "leed", "meed", "reed", "seed", "speed", "steed","bring", "king", "sing", "spring", "swing", "wing", "zing", "bling", "cling", "ding", "fling", "ging", "ling", "ming", "ping", "ring", "sling", "ting", "ving", "bing", "cing", "ding", "fing", "ging", "hing", "jing", "king", "ling", "ming", "ning", "ping", "qing", "ring", "sing", "ting", "ving", "wing", "xing", "ying", "zwing"]


    # Debug print statement to check if summary ends with a full stop
    print("Does summary end with a full stop?", summary.endswith("."))

    endfullstop = summary.endswith(".")

    # If summary doesn't end with a full stop
    if not endfullstop:
        num_errors += 1
        errors.append("Summary doesn't end with a full stop.")

        # Get the last word in the summary
        words = summary.split()
        last_word = words[-1]

        # Find the start and end index of the last word in the original summary
        # Use rfind to locate the start of the last word
        start_index = summary.rfind(last_word)
        end_index = start_index + len(last_word)

        # Append the last word and its indices to the respective arrays
        grammar_mistakes.append(last_word)
        grammatical_indices.append((start_index, end_index, "Summary doesn't end with a full stop."))


    
    # Check for ' .' instead of '.'
    if ' .' in summary:
        num_errors += summary.count(' .')
        errors.append("Space before period")
        # Add words causing the error to grammar_mistakes array
        matches = re.finditer(r'(\w+) \.', summary)
        for match in matches:
            start_index = match.start()
            end_index = match.end()
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index,"Space before period"))



    # Check for ' ,' instead of ','
    if ' ,' in summary:
        num_errors += summary.count(' ,')
        errors.append("Space before Comma")
        # Add words causing the error to grammar_mistakes array
        matches = re.finditer(r'(\w+) \,', summary)
        for match in matches:
            start_index = match.start(1)
            end_index = match.end(0)
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index, "Space before Comma"))
            

    # Check for continuous occurrences of the same punctuation mark
    # Matches sequences where the same punctuation mark repeats, allowing for optional spaces
    punctuation_matches = re.finditer(r'([^\w\s])(\s*\1)+', summary)
    for match in punctuation_matches:
        start_index = match.start(0)
        end_index = match.end(0)
        num_errors += 1
        errors.append("Repeated punctuation marks")
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append((start_index, end_index, "Repeated punctuation marks"))
    
    
    # Words considered errors
    incorrect_words = ['fishes', 'peoples', 'leafs', 'gooses', 'shrimps']

    # Check if any of these words appear in the summary
    for word in incorrect_words:
        if word in summary:
            num_errors += summary.count(word)
            errors.append(f"Incorrect word usage: {word}")
            # Find occurrences of the incorrect word in the summary
            matches = re.finditer(r'\b' + re.escape(word) + r'\b', summary)
            for match in matches:
                start_index = match.start()
                end_index = match.end()
                grammar_mistakes.append(summary[start_index:end_index])
                grammatical_indices.append((start_index, end_index, f"Incorrect plural word usage: {word}"))

    
    # Define the array of accepted repeated words
    allowed_repeated_words = [
    "had had", "that that", "the the", "is is", "it it", "do do", "you you", "are are",
    "was was", "will will", "would would", "if if", "on on", "at at", "in in", "has has",
    "to to", "from from", "as as", "by by", "he he", "we we", "they they", "go go", "no no",
    "why why", "how how"]

    # Check for repeated words (same word occurring twice continuously)
    matches = re.finditer(r'\b(\w+)\b\s+\1\b', summary)
    for match in matches:
        repeated_word = match.group(0).lower()  # get the repeated word
        if repeated_word not in allowed_repeated_words:  # if not in allowed list
            start_index = match.start(0)
            end_index = match.end(0)
            num_errors += 1
            errors.append("Repeated word")
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index, "Repeated word"))


    # Check for "can" followed by a plural word
    # if 'can' in summary:
    #     matches = re.finditer(r'can (\w+s\b)', summary)
    #     for match in matches:
    #         start_index = match.start(0)
    #         end_index = match.end(1)
    #         num_errors += 1
    #         errors.append("Word 'can' followed by a plural form")
    #         grammar_mistakes.append(summary[start_index:end_index])
    #         grammatical_indices.append((start_index, end_index))


    # Check if 'a' word appears in lowercase
    word_to_check = 'i'
    if word_to_check.lower() in summary:
        matches = re.finditer(r'\b' + re.escape(word_to_check) + r'\b', summary)
        for match in matches:
            if match.group(0) == word_to_check.lower():
                start_index = match.start(0)
                end_index = match.end(0)
                num_errors += 1
                errors.append(f"Word '{word_to_check}' appears in lowercase")
                grammar_mistakes.append(summary[start_index:end_index])
                grammatical_indices.append((start_index, end_index, f"Word '{word_to_check}' appears in lowercase"))

  
    # # Check for "to" followed by a non-base form of a verb
    # if 'to' in summary:
    #     # Check for "due to"
    #     matches_due_to = re.finditer(r'due to (\w+)', summary)
    #     for match in matches_due_to:
    #         verb = match.group(1)
    #         if (verb.endswith('ed') and verb not in ed_ing_words):
    #             start_index = match.start(0)
    #             end_index = match.end(0)
    #             num_errors += 1
    #             errors.append("Word 'to' followed by a non-base form of a verb")
    #             grammar_mistakes.append(summary[start_index:end_index])
    #             grammatical_indices.append((start_index, end_index))

    #     # Check for normal "to"
    #     matches_to = re.finditer(r'(?<!due )to (\w+)', summary)
    #     for match in matches_to:
    #         verb = match.group(1)
    #         if (verb.endswith('ed') and verb not in ed_ing_words):
    #             start_index = match.start(0)
    #             end_index = match.end(0)
    #             num_errors += 1
    #             errors.append("Word 'to' followed by a non-base form of a verb")
    #             grammar_mistakes.append(summary[start_index:end_index])
    #             grammatical_indices.append((start_index, end_index))


    # errors.append(spell_errors)
    # Check for missing space after comma
    if ',' in summary:
        comma_indices = [i for i, char in enumerate(summary) if char == ',']
        for comma_index in comma_indices:
            # Check if there's a character right after the comma
            if comma_index + 1 < len(summary):
                next_char = summary[comma_index + 1]
                # Ignore if the next character is a space or a special character
                if next_char != ' ' and not next_char.isalnum():
                    continue
                # Check for missing space only if the next character is alphanumeric
                if next_char != ' ':
                    num_errors += 1
                    errors.append("Missing space after comma")
                    # Add the word causing the error to grammar_mistakes array
                    word = re.findall(r',\s*(\w+)', summary[comma_index:])
                    if word:
                        grammar_mistakes.append((word[0]))
                        grammatical_indices.append((comma_index, comma_index + 1 + len(word[0]), "Missing space after comma"))



    sentence_boundary_regex = re.compile(r'[.!?]\s')  # regex to identify sentence boundaries
    paragraph_boundary_regex = re.compile(r'\n\s*')

    # Find all sentence boundaries
    sentence_boundaries = [m.end() for m in sentence_boundary_regex.finditer(doc.text)]

    # Find all paragraph boundaries
    paragraph_boundaries = [m.end() for m in paragraph_boundary_regex.finditer(doc.text)]


    # Merge sentence and paragraph boundaries into one list for easy checking
    all_boundaries = sorted(set(sentence_boundaries + paragraph_boundaries))
    first_word_index = 0

    quote_level = 0
    bracket_level = 0
    in_quotes = False
    in_brackets = False

    for token in doc:
        # Initialize variables to track mistake indices
        mistake_start_idx = token.idx
        mistake_end_idx = token.idx + len(token.text)

        # Skip if the token is a proper noun
        # if token.tag_ == 'NNP':
        #     continue
        # Get the token's start index in the text
        token_start = token.idx

        # Check if the token is at the beginning of a sentence or paragraph
        is_first_word = any(sb == token_start for sb in all_boundaries)

        # If the word is "i", skip this check
        if token.text.lower() in ['i','dna']:
            continue

        # Update quote and bracket levels
        if token.text in ['"', "'"]:
            quote_level += 1
            if quote_level % 2 == 1:
                in_quotes = True
            else:
                in_quotes = False
        elif token.text in ['[', '(']:
            bracket_level += 1
            in_brackets = True
        elif token.text in [']', ')']:
            bracket_level -= 1
            if bracket_level == 0:
                in_brackets = False
        


        # Check if it's the first word in the document
        is_first_word_in_doc = token_start == first_word_index

        # Check if the token is at the beginning of a sentence
        is_first_word_in_sentence = any(sb == token_start for sb in sentence_boundaries)

        # Rule: If the word is capitalized and it's not the first word in a sentence, it's an error
        if token.tag_ != 'NNP' and token.text[0].isupper() and not in_quotes and not in_brackets and not is_first_word_in_sentence and not is_first_word and not is_first_word_in_doc:
            if token.text.lower() in ['latin','x-ray','x']:
                continue
            num_errors += 1
            errors.append(f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence")
            grammar_mistakes.append((token.text))
            grammatical_indices.append((token_start, token_start + len(token.text), f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence"))



        # Rule 1: Proper noun should not be lower case
        if token.tag_ == 'NNP' and token.text.islower() and token.text not in ["physics","considereng","learning"]:
            num_errors += 1
            errors.append(f"Lowercase proper noun: '{token.text}'")
            grammar_mistakes.append((token.text))
            grammatical_indices.append((mistake_start_idx, mistake_end_idx, f"Lowercase proper noun: '{token.text}'"))

        # Rule 2: Use of 'whom' instead of 'who' in subject position
        if token.text.lower() == 'whom' and (token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass'):
            num_errors += 1
            errors.append("Use of 'whom' instead of 'who' in subject position")
            grammar_mistakes.append(('whom'))
            grammatical_indices.append((mistake_start_idx, mistake_end_idx, "Use of 'whom' instead of 'who' in subject position"))

        # Rule 3: Incorrect use of apostrophes ('s vs. s')
        if token.text == "'s":
            previous_token = token.nbor(-1)
            # Check if the token is not attached to a noun

            if token.head.pos_ in ['NUM'] and token.head.text !='one':
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for numbers.")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx, "Incorrect use of apostrophe ('s) for numbers."))

            # Check if the token is not attached to a noun
            elif token.head.pos_ not in ['NOUN', 'PROPN', 'PRON', 'VERB', 'NUM', 'AUX']:
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx, "Incorrect use of apostrophe ('s) for non-nouns"))

            

            elif token.head.pos_ in ['NUM'] and token.head.text !='one':
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx, "Incorrect use of apostrophe ('s) for non-nouns"))


            # # Check if the token is attached to a plural noun
            # elif token.head.tag_ == 'NNS':
            #     num_errors += 1
            #     errors.append("Incorrect use of apostrophe ('s) for plural nouns")
            #     errors.append(token)
            #     grammar_mistakes.append((previous_token.text + token.text))
            #     grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx))

            # Check if the token is attached to a proper noun
            elif token.head.tag_ == 'NNP' and not token.dep_ in ['poss','case']:
                print("TOKEN DEP::", token.dep_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for proper nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx, "Incorrect use of apostrophe ('s) for proper nouns"))


        # Rule 4: Check for conjunction errors
        if token.pos_ == 'CCONJ':
            head = token.head
            allowed_head_pos = ['NOUN', 'PRON', 'ADJ', 'ADV', 'ADP', 'DET', 'CCONJ', 'SCONJ', 'INTJ', 'SYM', 'VERB', 'AUX', 'PROPN']
            # print("TEXT::", token.text)
            if head.pos_ not in allowed_head_pos:
                print("HEAD POS::", head.pos_)
                print("TEXT::", token.text)
                num_errors += 1
                errors.append("Conjunction error: Incorrect use of conjunction")
                grammar_mistakes.append((token.text))
                grammatical_indices.append((mistake_start_idx, mistake_end_idx, "Conjunction error: Incorrect use of conjunction"))


        # # Rule 4: Misplaced modifier
        # if token.dep_ == 'advmod' and token.head.tag_ != 'JJ':
        #     num_errors += 1
        #     errors.append("Misplaced modifier: adverb modifying wrong word")
        #     errors.append(token)
        # Rule 5: Check for 'a' before words with vowel sounds
        if token.text.lower() == 'a':
            next_token = token.nbor()
            if next_token.text.lower() in vowels_not_starting_with_vowels:
                num_errors += 1
                errors.append("Use of 'a' before a word with a vowel sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text), "Use of 'a' before a word with a vowel sound"))

            elif next_token.text[0].lower() in 'aeiou' and next_token.text.lower() not in words_with_consonant_sound:
                num_errors += 1
                errors.append("Use of 'a' before a word with a vowel sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text), "Use of 'a' before a word with a vowel sound"))

        # Rule 6: Check for 'an' before words with consonant sounds
        if token.text.lower() == 'an':
            next_token = token.nbor()
            if next_token.text.lower() in vowels_not_starting_with_vowels:
                pass
            elif next_token.text.lower() in words_with_consonant_sound or next_token.text[0].lower() not in 'aeiou':
                num_errors += 1
                errors.append("Use of 'an' before a word with a consonant sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text),"Use of 'an' before a word with a consonant sound"))

        
        # # Rule 7: Check for 'an' before words with vowel sounds
        # if token.text.lower() != 'an':
        #     next_token = token.nbor()
        #     if next_token.text.lower() not in vowels_not_starting_with_vowels and (next_token.text[0].lower() in 'aeiou' or next_token.text.lower() in words_with_consonant_sound):
        #         num_errors += 1
        #         errors.append("Missing 'an' before a word with a vowel sound")
        #         grammar_mistakes.append((next_token.text))
        #         grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text)))

        # Rule 7: Check for punctuation mistakes
        if token.pos_ == 'PUNCT':
            if token.text not in ['.', ',', '!', '?', ':', ';', '“', '”', '‘', '’', '—', '–', '-', '"', "'", '(', ')', '[', ']', '{', '}', '/', '\\', '_', '*', '&', '@', '#', '$', '%', '^', '<', '>', '|', '`', '~', '+', '=', '...', '..', '¿', '¡']:
                num_errors += 1
                errors.append(f"Unexpected punctuation: '{token.text}'")
                grammar_mistakes.append((token.text))
                grammatical_indices.append((mistake_start_idx, mistake_end_idx, f"Unexpected punctuation: '{token.text}'"))


    # Convert the list of lists to a list of tuples for easier comparison
    indices_tuples = [tuple(indices) for indices in grammatical_indices]

    # Remove duplicate words
    unique_mistakes = list(set(grammar_mistakes))

    # Count the number of duplicates
    num_duplicates = len(indices_tuples) - len(set(indices_tuples))

    # Remove the duplicates
    unique_indices = list(set(indices_tuples))
    unique_indices = [list(indices) for indices in unique_indices]

    print("Number of duplicates removed:", num_duplicates)
    print("Unique grammatical indices:", unique_indices)

    num_errors-= num_duplicates

    print("Number of grammatical errors:", num_errors)
    if num_errors > 0:
        print("Grammatical errors detected:")
        for error in errors:
            print("-", error)

    if num_errors >= 1 and num_errors < 3:
        score -= 0.5
    elif num_errors >= 3 and num_errors <= 5:
        score -= 1.0
    elif num_errors > 5:
        score -= 2.0

    score = max(score, 0)

    grammatical_indices= unique_indices
    grammar_mistakes = unique_mistakes
    return score, grammar_mistakes, grammatical_indices



def calculate_form_score_core(summary):
    form_score = 2.0
    num_words = len(summary.split())  # Counting words by splitting on whitespace
    
    # Stripping whitespace characters from the end of the summary
    summary = summary.strip()

    # Debug print statement to check if summary ends with a full stop
    # print("Does summary end with a full stop?", summary.endswith("."))
    
    # Checking conditions
    if num_words < 5 or num_words > 60:
        form_score = 0.0
    elif num_words >= 25 and num_words <= 50:
        form_score = 2.0
    else:
        form_score = 1.0
    
    # Checking additional conditions
    if summary.isupper() or not any(c.isalnum() for c in summary) or summary.startswith("•"):
        form_score = 0.0
        
    return form_score


def calculate_form_score_academic(summary):
    form_score = 1.0
    num_words = len(summary.split())  # Counting words by splitting on whitespace

    # Stripping whitespace characters from the end of the summary
    summary = summary.strip()

    # Checking conditions
    if num_words < 5 or num_words > 75 or summary.isupper():
        form_score = 0.0

    # Checking additional conditions
    if len(summary.split('. ')) > 1:
        form_score = 0.0

    return form_score


# Define function with default initialization of vocab_range_score
def calculate_vocab_range_score(summary, accent, grammar_score, grammatical_indices):
    words = word_tokenize(summary.lower())
    unique_words = set(words)
    num_errors, spell_errors, misspelled_indices = calculate_spelling_score(summary, accent, grammatical_indices)
    spellers= len(misspelled_indices)
    print("Misspelled Indices::", spellers)
    # Initialize vocab_range_score to avoid unbound local variable error
    vocab_range_score = 0  # Default initialization

    if len(words) > 0:  # Check if there are words
        if grammar_score == 0.0:
            vocab_range_score = 1 * len(unique_words) / len(words)  # Scale adjustment
            print("VOCAB RANGE SCORE", vocab_range_score)  
        else:
            vocab_range_score = 2 * len(unique_words) / len(words)  # Scale adjustment
            print("VOCAB RANGE SCORE", vocab_range_score)    

        # print("OUTSIDE VOCAB RANGE SCORE::", vocab_range_score)
        # # Rounding and further processing
        # rounded_score = round(vocab_range_score, 1)

        # print("ROUNDED SCORE", rounded_score)
        # updated_score = round(rounded_score * 4) / 4
        # print("Updated Round Score::", updated_score)
        # updated_score -= spellers * 0.5
        # print("Num Errors Round Score::", updated_score)

        if vocab_range_score >0 and vocab_range_score <=1:
            vocab_range_score = 1.0

        if vocab_range_score >1 and vocab_range_score <=2:
            vocab_range_score = 2.0

        updated_score = max(vocab_range_score, 0)  # Ensure non-negative
    else:
        # If there are no words, define a default score or action
        updated_score = 0  # No words, score is zero
    
    # Error-related outputs
    print("NUMBER OF ERRORS:", num_errors)
    for i in spell_errors:
        print("MISSPELLED:", i)

    return updated_score, spell_errors, misspelled_indices



def score_summary(passage, summary, pte_type, accent):
    print("Pte Type:", pte_type)
    content_score = calculate_content_score_summary(passage, summary)
    print("content score: ",content_score)
    grammar_score, grammar_mistakes, grammatical_indices = calculate_grammar_score(summary , accent)
    print("grammer score: ",grammar_score)
    if pte_type == "pte core":
        form_score = calculate_form_score_core(summary)
        print("form score: ",form_score)
    elif pte_type == "pte academic":
        form_score = calculate_form_score_academic(summary)
        print("form score: ",form_score)
    vocab_range_score, spell_errors, misspelled_indices = calculate_vocab_range_score(summary, accent, grammar_score, grammatical_indices)
    print("vocab range score: ", vocab_range_score)
    comments= set_summary_comments(content_score ,form_score , grammar_score , vocab_range_score, pte_type)
    print("Comments::" , comments)
    total_score = content_score + grammar_score + form_score + vocab_range_score
    return total_score, content_score, grammar_score, form_score, vocab_range_score, comments, spell_errors , grammar_mistakes, misspelled_indices, grammatical_indices


