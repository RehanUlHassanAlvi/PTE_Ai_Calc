import re
import nltk
from nltk.tokenize import word_tokenize
import spacy
import enchant
from comments.summarizespokensumary_commnts import set_summarizespoken_comments
from nltk.corpus import stopwords
from collections import Counter, defaultdict
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



def merge_phrases(phrases):
    merged_phrases = defaultdict(int)

    # Convert phrases to a list of (phrase, count) for easy manipulation
    phrase_list = list(phrases.items())

    while phrase_list:
        # Take the first phrase and initialize the merged phrase and count
        base_phrase, base_count = phrase_list.pop(0)
        merged_phrase = base_phrase
        merged_count = base_count

        # Check for overlaps with the remaining phrases
        for i in range(len(phrase_list) - 1, -1, -1):
            current_phrase, current_count = phrase_list[i]
            base_words = base_phrase.split()
            current_words = current_phrase.split()

            # Find overlap and merge phrases
            overlap_index = None
            for j in range(1, min(len(base_words), len(current_words)) + 1):
                if base_words[-j:] == current_words[:j]:
                    overlap_index = j
            
            if overlap_index:
                merged_phrase = ' '.join(base_words + current_words[overlap_index:])
                merged_count += current_count
                phrase_list.pop(i)

        # Add the merged phrase and its count to the merged_phrases dictionary
        merged_phrases[merged_phrase] += merged_count

    return dict(merged_phrases)


def find_recurring_phrases(text, n=3, skip_phrases=None):

    print("Skip Phrases::", skip_phrases)
    """
    Finds all phrases of length 'n' or greater in a given text and counts their occurrences,
    ensuring that phrases do not span across sentence boundaries.
    """
    tmpWord = 'also'
    pattern = rf'\b{tmpWord}\b'
    # Remove the word using re.sub
    cleaned_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Remove any extra spaces left after word removal
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()    
    # Split the text into sentences
    sentences = nltk.sent_tokenize(cleaned_text.lower())
    
    all_n_grams = []

    # For each sentence, generate n-grams
    for sentence in sentences:
        # Tokenize the sentence into words and remove punctuation
        words = nltk.word_tokenize(sentence)
        words = [w for w in words if w.isalnum()]  # Keep only alphanumeric tokens
        
        # Create n-grams of the given length
        n_grams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1) if " ".join(words[i:i+n]) not in skip_phrases]
        # if n_grams not in skip_phrases:
        all_n_grams.extend(n_grams)  # Add to the complete list of n-grams
    
    print("N GRAM::", n_grams)
    # Count the occurrences of each n-gram
    n_gram_counts = Counter(all_n_grams)
    
    # Return the phrases that appear more than once and have at least 'n' words
    return {k: v for k, v in n_gram_counts.items() if v > 1 and len(k.split()) >= n}


def calculate_content_score_summary(passage, summary):
    updated_score = 2.0
    
    # Tokenize the passage into paragraphs and then into tokens
    paragraphs = passage.split("\n")  # Splitting the passage into paragraphs
    
    # Tokenize the summary into sentences
    summary_sentences = summary.split(".")  # Splitting the summary into sentences based on full stops
    summary_sentences = [sentence for sentence in summary_sentences if sentence.strip()]  # Remove empty sentences

    # Remove punctuation and stopwords from summary tokens
    stop_words = set(stopwords.words('english'))
    tokenized_summary_sentences = [nltk.word_tokenize(sentence.lower()) for sentence in summary_sentences]
    tokenized_summary_sentences = [[token for token in sentence if token.isalnum() and token not in stop_words] for sentence in tokenized_summary_sentences]

    # List to store minor aspects from each paragraph
    paragraph_minor_aspects = []
    
    for paragraph in paragraphs:
        # Tokenize each paragraph
        paragraph_tokens = nltk.word_tokenize(paragraph.lower())
        paragraph_tokens = [token for token in paragraph_tokens if token.isalnum()]

        # Remove major aspects, stopwords, and numeric tokens
        paragraph_tokens = [token for token in paragraph_tokens if token not in stop_words and not token.isdigit()]

        # Add unique minor aspects from each paragraph
        paragraph_minor_aspects.append(list(set(paragraph_tokens)))
    
    matched_tokens = set()
    
    total_matched_tokens = 0
    
    for sentence_tokens in tokenized_summary_sentences:
        sentence_matched_tokens = set()
        for minor_aspects in paragraph_minor_aspects:
            # Match tokens in the sentence with paragraph tokens
            sentence_matched_tokens.update(set(sentence_tokens) & set(minor_aspects))
        matched_tokens.update(sentence_matched_tokens)
        # Limit the number of matched tokens to 4 per sentence
        sentence_matched_tokens = list(sentence_matched_tokens)[:4]
        total_matched_tokens += len(sentence_matched_tokens)
    length_matched = total_matched_tokens

    
    # length_matched = len(matched_tokens)
    print("Matched Tokens::", length_matched)

    phrases_to_check = ["I hear from", "I heard from", "I also heard from", "I also hear from", "I heard that", "I also heard that",
                        "i hear from", "i heard from", "i also heard from", "i also hear from", "i heard that", "i also heard that",
                        "he hears from", "he heard from", "he also heard from", "he also hears from", "he heard that", "he also heard that",
                        "she hears from", "she heard from", "she also heard from", "she also hears from", "she heard that", "she also heard that",
                        "they hear from", "they heard from", "they also heard from", "they also hear from", "they heard that", "they also heard that",
                        "he talked about", "he also talked about", "he talks about", "she talked about", "she also talked about", "she talks about",
                        "they talked about", "they also talked about", "they talk about", "I talked about", "I also talked about", "I talk about",
                        "i talked about", "i also talked about", "i talk about", "he explained about", "he also explained about", "he explains about", 
                        "she explained about", "she also explained about", "she explains about", "she explained that", "she also explained that", "she explains that",
                        "he explained that", "he also explained that", "he explains that","they explained that", "they also explained that", "they explain that",
                        "they explaind about", "they also explained about", "they explain about", "I explained about", "I also explained about", "I explain about",
                        "i explained about", "i also explained about", "i explain about", "i also explain about", "I also explain about"
                        ]
    skip_phrases1 = phrases_to_check + ["also heard that", "also heard from", "also hear from","i also heard", "i also hear", "I also heard", "I also hear", "also talked about", "also explained about", "i also explained", "I also explained", "also explain about"]

    num_occurrences = 0
    occurrences = []

    for phrase in phrases_to_check:
        matches = re.finditer(r'\b' + re.escape(phrase) + r'\b', summary)
        for match in matches:
            start_index = match.start()
            end_index = match.end()
            num_occurrences += 1
            occurrences.append((phrase, summary[start_index:end_index]))

    print("Occurences::", occurrences)
    print("Number of Occurences::", num_occurrences)
    if num_occurrences > 0:
        num_occurrences -= 1
    print("Number of Occurences::", num_occurrences)
    # Find recurring phrases in the summary
    recurring_phrases = find_recurring_phrases(summary, n=3, skip_phrases=skip_phrases1)

    print("Recurring Phrases::", recurring_phrases)

    recurring_phrases1 = merge_phrases(recurring_phrases)

    print("Merged Recurring Phrases::", recurring_phrases1)

    count1 = len(recurring_phrases1)

    print("Count1::", count1)
    # Create a new dictionary with adjusted counts
    adjusted_dict = {key: value - 1 for key, value in recurring_phrases.items()}

    total_sum = sum(adjusted_dict.values())

    # print("Total Sum::", total_sum)
    # if num_occurrences > 0:
    #     total_sum += num_occurrences

    # Deduction based on matched tokens
    if length_matched >= 10:
        updated_score -= 0  # No deduction
    elif 7 <= length_matched <= 9:
        updated_score -= 0.25
    elif 4 <= length_matched <= 6:
        updated_score -= 0.5
    elif 1 <= length_matched <= 3:
        updated_score -= 0.75
    else:
        updated_score -= 1

    print("C1 Score::", updated_score)

    # print("Total Sum::", total_sum)
    num_occurrences += count1
    print("Minus Occurences::", num_occurrences)

    if num_occurrences >=0:
        updated_score -= (num_occurrences* 0.5)

    print("C2 Score::", updated_score)

    # Calculate percentage of sentences containing at least 2 aspects
    length_summary = len(summary_sentences)
    print("LENGTH::", length_summary)
    if length_summary == 1 or length_summary == 0:  # If the summary is written in a single sentence
        updated_score -= 1  # Deduct 1 mark
    else:
        sentences_with_at_least_2_aspects = 0
        for sentence_tokens in tokenized_summary_sentences:
            if len(set(sentence_tokens) & set(matched_tokens)) >= 2:
                sentences_with_at_least_2_aspects += 1
        percentage = (sentences_with_at_least_2_aspects / length_summary) * 100
        print("PERCENTAGE::", percentage)
        if percentage >= 90:
            print("NO PERCENTAGE DEDUCTION.")
            updated_score -= 0
        elif 75 <= percentage < 90:
            print("0.25 PERCENTAGE DEDUCTION.")
            updated_score -= 0.25
        elif 50 <= percentage < 75:
            print("0.50 PERCENTAGE DEDUCTION.")
            updated_score -= 0.50
        elif 36 <= percentage < 50:
            print("0.75 PERCENTAGE DEDUCTION.")
            updated_score -= 0.75
        else:
            print("1 PERCENTAGE DEDUCTION.")
            updated_score -= 1

    print("C1 Score::", updated_score)
    updated_score = max(updated_score, 0)
    updated_score = round(updated_score, 2)

    # updated_score = min(updated_score, 2)
    print("C1 Score::", updated_score)
    return updated_score


def calculate_spelling_score(summary, accent, grammatical_indices):
    print("ACCENT:::", accent)
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
                print("Gram: ===",grammatical_indices)
                # Check if the starting or ending index of the misspelled word matches with any grammatical index
                print("Gram: ===", grammatical_indices)

                if any((len(gi) == 3 and (start_index == gi[0] or end_index == gi[1])) or 
                    (len(gi) == 2 and (start_index == gi[0] or end_index == gi[1])) for gi in grammatical_indices):
                    # your logic here

                    continue  # Skip counting the misspelled word and excluding it from the corrected words
                if word.lower() in WORD_LIST:
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
            grammatical_indices.append((start_index, end_index,"Space before Comma"))
            

    # Check for continuous occurrences of the same punctuation mark
    # Matches sequences where the same punctuation mark repeats, allowing for optional spaces
    punctuation_matches = re.finditer(r'([^\w\s])(\s*\1)+', summary)
    for match in punctuation_matches:
        start_index = match.start(0)
        end_index = match.end(0)
        num_errors += 1
        errors.append("Repeated punctuation marks")
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append((start_index, end_index,"Repeated punctuation marks"))
    
    
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
                grammatical_indices.append((start_index, end_index,f"Incorrect word usage: {word}"))

    
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
            grammatical_indices.append((start_index, end_index,"Repeated word"))


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
                grammatical_indices.append((start_index, end_index,f"Word '{word_to_check}' appears in lowercase"))

  
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
                        grammatical_indices.append((comma_index, comma_index + 1 + len(word[0]),"Missing space after comma"))



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

    # Assuming `doc` is the parsed document using spaCy or a similar NLP tool

    for idx, token in enumerate(doc):
        if token.tag_ == 'NNP' and token.text in ["Resilience"]:
            # Check if it's the first word or comes after a full stop
            if idx == 0 or (idx > 0 and doc[idx - 1].text == '.'):
                continue
            print(token.text)
            num_errors += 1
            errors.append(f"Extra Capitalization: '{token.text}'")
            grammar_mistakes.append((token.text))
            mistake_start_idx = token.idx
            mistake_end_idx = token.idx + len(token.text)
            grammatical_indices.append((mistake_start_idx, mistake_end_idx,f"Extra Capitalization: '{token.text}'"))


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
            if token.text in ['Latin','X-ray','X']:
                continue
            num_errors += 1
            errors.append(f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence")
            grammar_mistakes.append((token.text))
            grammatical_indices.append((token_start, token_start + len(token.text),f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence"))

        # if token.tag_ == 'NNP' and token.text in ["Resilience"]:
        #     print(token.text)
        #     num_errors += 1
        #     errors.append(f"Extra Capitalization: '{token.text}'")
        #     grammar_mistakes.append((token.text))
        #     grammatical_indices.append((mistake_start_idx, mistake_end_idx))


        # Rule 1: Proper noun should not be lower case
        if token.tag_ == 'NNP' and token.text.islower() and token.text not in ["physics","considereng"]:
            print(token.text)
            num_errors += 1
            errors.append(f"Lowercase proper noun: '{token.text}'")
            grammar_mistakes.append((token.text))
            grammatical_indices.append((mistake_start_idx, mistake_end_idx,f"Lowercase proper noun: '{token.text}'"))

        # Rule 2: Use of 'whom' instead of 'who' in subject position
        if token.text.lower() == 'whom' and (token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass'):
            num_errors += 1
            errors.append("Use of 'whom' instead of 'who' in subject position")
            grammar_mistakes.append(('whom'))
            grammatical_indices.append((mistake_start_idx, mistake_end_idx),"Use of 'whom' instead of 'who' in subject position")

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
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx,"Incorrect use of apostrophe ('s) for numbers."))

            # Check if the token is not attached to a noun
            elif token.head.pos_ not in ['NOUN', 'PROPN', 'PRON', 'VERB', 'NUM', 'AUX']:
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx,"Incorrect use of apostrophe ('s) for non-nouns"))

            

            elif token.head.pos_ in ['NUM'] and token.head.text !='one':
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx,"Incorrect use of apostrophe ('s) for non-nouns"))


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
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx,"Incorrect use of apostrophe ('s) for proper nouns"))


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
                grammatical_indices.append((mistake_start_idx, mistake_end_idx,"Conjunction error: Incorrect use of conjunction"))


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
                grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text),"Use of 'a' before a word with a vowel sound"))

            elif next_token.text[0].lower() in 'aeiou' and next_token.text.lower() not in words_with_consonant_sound:
                num_errors += 1
                errors.append("Use of 'a' before a word with a vowel sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append((next_token.idx, next_token.idx + len(next_token.text),"Use of 'a' before a word with a vowel sound"))

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
                grammatical_indices.append((mistake_start_idx, mistake_end_idx,f"Unexpected punctuation: '{token.text}'"))


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
    print("Number of Words:::",num_words)
    
    # Stripping whitespace characters from the end of the summary
    summary = summary.strip()

    # Debug print statement to check if summary ends with a full stop
    # print("Does summary end with a full stop?", summary.endswith("."))
    
    # Checking conditions
    if num_words < 5 or num_words > 40:
        form_score = 0.0
    elif num_words >= 20 and num_words <= 30:
        form_score = 2.0
    else:
        form_score = 1.0
    
    # Checking additional conditions
    if summary.isupper() or not any(c.isalnum() for c in summary) or summary.startswith("•"):
        form_score = 0.0
        
    return form_score


def calculate_form_score_academic(summary):
    form_score = 2.0
    num_words = len(summary.split())  # Counting words by splitting on whitespace
    print("Number of Words:::",num_words)

    # Stripping whitespace characters from the end of the summary
    summary = summary.strip()


    # Checking conditions
    if num_words < 40 or num_words > 100:
        form_score = 0.0
    elif num_words >= 50 and num_words <= 70:
        form_score = 2.0
    else:
        form_score = 1.0

    # Checking additional conditions
    if summary.isupper() or not any(c.isalnum() for c in summary) or summary.startswith("•"):
        form_score = 0.0

    # Checking additional conditions
    # if len(summary.split('. ')) > 1:
    #     form_score = 0.0

    print("FORM SCORE::", form_score)
    return form_score


# Define function with default initialization of vocab_range_score
def calculate_vocab_range_score(summary, grammar_score):
    words = word_tokenize(summary.lower())
    unique_words = set(words)
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
    

    return updated_score



def summarizespoken_summary(passage, summary, pte_type, accent):
    content_score = calculate_content_score_summary(passage, summary)
    print("content score: ",content_score)
    grammar_score, grammar_mistakes, grammatical_indices = calculate_grammar_score(summary , accent)
    print("grammer score: ",grammar_score)
    spelling_score, correct_words, misspelled_indices = calculate_spelling_score(summary, accent, grammatical_indices)
    print("Spelling Score:", spelling_score)
    if pte_type == "pte core":
        form_score = calculate_form_score_core(summary)
        print("form score: ",form_score)
    elif pte_type == "pte academic":
        form_score = calculate_form_score_academic(summary)
        print("form score: ",form_score)
    vocab_range_score = calculate_vocab_range_score(summary, grammar_score)
    print("vocab range score: ", vocab_range_score)
    comments= set_summarizespoken_comments(content_score ,form_score , grammar_score , vocab_range_score, pte_type, spelling_score)
    print("Comments::" , comments)
    print("I AM FORM SCORE::", form_score)
    if form_score == 0 or content_score == 0:
        print("00000000000000000000000")
        total_score = 0
        content_score = 0
        grammar_score = 0
        form_score = 0
        vocab_range_score = 0
        spelling_score = 0

    total_score = content_score + grammar_score + form_score + vocab_range_score + spelling_score
    return total_score, content_score, grammar_score, form_score, vocab_range_score, comments, correct_words, grammar_mistakes, misspelled_indices, grammatical_indices, correct_words, spelling_score


