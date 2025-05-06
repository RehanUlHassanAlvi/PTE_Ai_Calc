import nltk
from nltk.tokenize import word_tokenize
import spacy
import numpy as np
import re
from collections import Counter
import string 
import enchant
from comments.essay_comments import set_essay_comments
from helper_functions.essay_content_score_helper import remove_punctuation_and_lower,detect_values_with_spaces,stem_words,generate_word_status_for_major_dict,generate_word_status_for_minor_dict,generate_word_status_dict_for_major_and_minor_for_less_para,scoring,generate_multiword_status_for_major_dict,generate_multiword_status_for_minor_dict,generate_all_words_aspects_dict, stem_words2
from helper_functions.essay_grammer_score_helper import merge_appos_words,count_multiple_spaces
from constants import WORD_LIST
# nltk.download('stopwords', download_dir='nltk_data/')
# nltk.download('vader_lexicon', download_dir='nltk_data/')
nltk.data.path.append('nltk_data/')
nltk.download('stopwords')
from nltk.corpus import stopwords

stopwords = set(stopwords.words('english'))


def update_dict_recursively(original_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict):
            original_dict[key] = update_dict_recursively(original_dict.get(key, {}), value)
        elif isinstance(value, list):
            original_dict[key] = value
        else:
            original_dict[key] = value
    return original_dict

def convert_to_2d(array):
    # Check if array is 3D by examining if the first element is a list of lists
    if len(array) > 0 and isinstance(array[0], list) and isinstance(array[0][0], list):
        # Flatten the 3D array into a 2D array
        return_arr = []
        for sublist in array:
          flat_array = np.array(sublist)
          
          # Perform element-wise OR operation across the rows
          combined_row = np.bitwise_or.reduce(flat_array, axis=0)          
          # Return the result as a list
          return_arr.append(combined_row.tolist())
        return return_arr
    else:
        # Return the array as it is if it's already 2D
        return array

def calculate_content_score(essay,question,major_aspect,minor_aspect):
    content_score = 3.0
    temp=essay
    
    copy_major_aspect = major_aspect[:]

    copy_minor_aspect=minor_aspect[:]


    main_string_no_punctuation_lower=remove_punctuation_and_lower(temp)
    question_no_punctuation_lower=remove_punctuation_and_lower(question)
    
    print("QUESTION::" ,question_no_punctuation_lower)
    # Count the occurrences of the question in the main string
    question_count = main_string_no_punctuation_lower.count(question_no_punctuation_lower)

    if question_count == 1:
        print("Question found once")
        content_score -= 1.0
    elif question_count == 2:
        print("Question found twice")
        content_score -= 2.0
    elif question_count >= 3:
        print("Question found three or more times")
        return 0.0
    

    
    # Define the conditions
    conditions = {
        "example": "example" in question_no_punctuation_lower,
        "advantages_disadvantages": ("advantages" in question_no_punctuation_lower) or ("disadvantages" in question_no_punctuation_lower),
        "agree_disagree": ("agree" in question_no_punctuation_lower) or ("disagree" in question_no_punctuation_lower),
        "positive_negative": ("positive" in question_no_punctuation_lower) or ("negative" in question_no_punctuation_lower)
    }

    # Iterate through each element in the minor_aspect array
    i = 0
    while i < len(minor_aspect):
        element = minor_aspect[i]
        
        # Check if the element is a list
        if isinstance(element, list):
            # Iterate through each word in the nested list
            j = 0
            while j < len(element):
                word = element[j]
                # Check if the word meets any of the specified conditions
                if conditions["example"] and word == "example":
                    element.remove(word)
                elif conditions["advantages_disadvantages"] and word in ["advantages", "disadvantages"]:
                    element.remove(word)
                elif conditions["agree_disagree"] and word in ["agree", "disagree"]:
                    element.remove(word)
                elif conditions["positive_negative"] and word in ["positive", "negative"]:
                    element.remove(word)
                else:
                    j += 1
            
            # Remove the nested list if it becomes empty after removing words
            if not element:
                minor_aspect.remove(element)
            else:
                i += 1
        else:
            # Check if the element meets any of the specified conditions
            if conditions["example"] and element == "example":
                minor_aspect.remove(element)
            elif conditions["advantages_disadvantages"] and element in ["advantages", "disadvantages"]:
                minor_aspect.remove(element)
            elif conditions["agree_disagree"] and element in ["agree", "disagree"]:
                minor_aspect.remove(element)
            elif conditions["positive_negative"] and element in ["positive", "negative"]:
                minor_aspect.remove(element)
            else:
                i += 1

    # Print the updated minor aspects
    print("Updated Minor Aspects:", minor_aspect)
    
    major_aspect_with_spaces=detect_values_with_spaces(major_aspect)
    minor_aspect_with_spaces=detect_values_with_spaces(minor_aspect)

    print("MINOR ASPECTS", minor_aspect_with_spaces)

    for value in major_aspect_with_spaces:
        major_aspect.remove(value)

    for value in minor_aspect_with_spaces:
        minor_aspect.remove(value)
    
    
    stemmed_major_aspect = stem_words(major_aspect)
    stemmed_minor_aspect = stem_words2(minor_aspect)

    print(stemmed_minor_aspect)

    essay=essay.replace("\n\n","\n")
    # essay = essay.replace(" .", " ")
    paragraphs = essay.split('\n')
    paragraphs = [s for s in paragraphs if s != ""]



    print("total paragraphs: ",len(paragraphs))


    if len(paragraphs)>=3:
        intro=paragraphs[0]
        conc=paragraphs[-1]
        body_values=paragraphs[1:-1]
        main_body = " ".join(body_values)

        intro = remove_punctuation_and_lower(intro)
        conc = remove_punctuation_and_lower(conc)
        main_body = remove_punctuation_and_lower(main_body)




        intro_words = intro.split()
        conc_words = conc.split()
        main_body_words = main_body.split()

        multi_word_major_aspect_dict=generate_multiword_status_for_major_dict(major_aspect_with_spaces,intro,conc,main_body)
        multi_word_minor_aspect_dict=generate_multiword_status_for_minor_dict(minor_aspect_with_spaces,intro,conc,main_body)

        stemmed_intro_words = stem_words(intro_words)
        stemmed_conc_words = stem_words(conc_words)
        stemmed_main_body_words = stem_words(main_body_words)


        main_body_major_aspect_counts = Counter(stemmed_main_body_words)

  
        main_body_minor_aspect_counts = Counter(stemmed_main_body_words)

        major_aspects_status_dict = generate_word_status_for_major_dict(stemmed_major_aspect, stemmed_intro_words, stemmed_conc_words, main_body_major_aspect_counts)
        minor_aspects_status_dict = generate_word_status_for_minor_dict(stemmed_minor_aspect, stemmed_intro_words, stemmed_conc_words, main_body_minor_aspect_counts)

        
        minor_aspects_status_dict = convert_to_2d(minor_aspects_status_dict)
        major_aspects_status_dict.update( multi_word_major_aspect_dict)
        minor_aspects_status_dict = update_dict_recursively(minor_aspects_status_dict, multi_word_minor_aspect_dict)
        
        # Check if the keyword "example" is in the question
        example_in_question = "example" in question_no_punctuation_lower

        # Check if "advantages" or "disadvantages" is in the question
        advantages_or_disadvantages_in_question = ("advantages" in question_no_punctuation_lower) or ("disadvantages" in question_no_punctuation_lower)

        # Check if "agree" or "disagree" is in the question
        agree_or_disagree_in_question = ("agree" in question_no_punctuation_lower) or ("disagree" in question_no_punctuation_lower)


        if example_in_question:
            # If "example" is in the question, check if "example" is mentioned in the body
            if "example" in main_string_no_punctuation_lower:
                print("Example mentioned in the body")
            else:
                print("Example not mentioned in the body")
                # Deduct content score if "example" is not mentioned in the body
                content_score -= 1.0


        if advantages_or_disadvantages_in_question:
            # If "advantages" or "disadvantages" is in the question, check if either is mentioned in the body
            if ("advantages" in main_string_no_punctuation_lower) or ("disadvantages" in main_string_no_punctuation_lower):
                print("Advantages or disadvantages mentioned in the body")
            else:
                print("Advantages or disadvantages not mentioned in the body")
                # Deduct content score if neither "advantages" nor "disadvantages" is mentioned in the body
                content_score -= 1.0



        if agree_or_disagree_in_question:
            # If "agree" or "disagree" is in the question, check if either is mentioned in the body
            if ("agree" in main_string_no_punctuation_lower) or ("disagree" in main_string_no_punctuation_lower):
                print("Agree or disagree mentioned in the body")
            else:
                print("Agree or disagree not mentioned in the body")
                # Deduct content score if neither "agree" nor "disagree" is mentioned in the body
                content_score -= 1.0


        # Check if "positive" or "negative" is in the question
        positive_or_negative_in_question = ("positive" in question_no_punctuation_lower) or ("negative" in question_no_punctuation_lower)

        if positive_or_negative_in_question:
            # If "positive" or "negative" is in the question, check if either is mentioned in the body
            if ("positive" in main_string_no_punctuation_lower) or ("negative" in main_string_no_punctuation_lower):
                print("Positive or negative mentioned in the body")
            else:
                print("Positive or negative not mentioned in the body")
                # Deduct content score if neither "positive" nor "negative" is mentioned in the body
                content_score -= 1.0



        score=scoring(major_aspects_status_dict,minor_aspects_status_dict,len(paragraphs),content_score)
        # print("content score: ",score)

    else:
        cscore = 3.0
        essay_words = essay.split()
        stemmed_essay_words = stem_words(essay_words)
        multi_word_major_aspect_dict,multi_word_minor_aspect_dict=generate_all_words_aspects_dict(major_aspect_with_spaces, minor_aspect_with_spaces,essay_words)

        major_aspects_status_dict, minor_aspects_status_dict=generate_word_status_dict_for_major_and_minor_for_less_para(stemmed_major_aspect,stemmed_minor_aspect ,stemmed_essay_words)

        major_aspects_status_dict.update( multi_word_major_aspect_dict)
        minor_aspects_status_dict.update( multi_word_minor_aspect_dict)

        # Check if the keyword "example" is in the question
        example_in_question = "example" in question_no_punctuation_lower

        # Check if "advantages" or "disadvantages" is in the question
        advantages_or_disadvantages_in_question = ("advantages" in question_no_punctuation_lower) or ("disadvantages" in question_no_punctuation_lower)

        # Check if "agree" or "disagree" is in the question
        agree_or_disagree_in_question = ("agree" in question_no_punctuation_lower) or ("disagree" in question_no_punctuation_lower)


        if example_in_question:
            # If "example" is in the question, check if "example" is mentioned in the body
            if "example" in main_string_no_punctuation_lower:
                print("Example mentioned in the body")
            else:
                print("Example not mentioned in the body")
                # Deduct content score if "example" is not mentioned in the body
                cscore -= 1.0


        if advantages_or_disadvantages_in_question:
            # If "advantages" or "disadvantages" is in the question, check if either is mentioned in the body
            if ("advantages" in main_string_no_punctuation_lower) or ("disadvantages" in main_string_no_punctuation_lower):
                print("Advantages or disadvantages mentioned in the body")
            else:
                print("Advantages or disadvantages not mentioned in the body")
                # Deduct content score if neither "advantages" nor "disadvantages" is mentioned in the body
                cscore -= 1.0



        if agree_or_disagree_in_question:
            # If "agree" or "disagree" is in the question, check if either is mentioned in the body
            if ("agree" in main_string_no_punctuation_lower) or ("disagree" in main_string_no_punctuation_lower):
                print("Agree or disagree mentioned in the body")
            else:
                print("Agree or disagree not mentioned in the body")
                # Deduct content score if neither "agree" nor "disagree" is mentioned in the body
                print("CCCCCCCCCCC",cscore)
                cscore -= 1.0
                print("CCCCCCCCCCC",cscore)


        # Check if "positive" or "negative" is in the question
        positive_or_negative_in_question = ("positive" in question_no_punctuation_lower) or ("negative" in question_no_punctuation_lower)

        if positive_or_negative_in_question:
            # If "positive" or "negative" is in the question, check if either is mentioned in the body
            if ("positive" in main_string_no_punctuation_lower) or ("negative" in main_string_no_punctuation_lower):
                print("Positive or negative mentioned in the body")
            else:
                print("Positive or negative not mentioned in the body")
                # Deduct content score if neither "positive" nor "negative" is mentioned in the body
                cscore -= 1.0


        score = scoring(major_aspects_status_dict, minor_aspects_status_dict,len(paragraphs),cscore)
        print("content score: ",score)
                

    return score


def calculate_grammar_score_essay(summary):
    print(summary)
    grammatical_indices = []
    
    count_double_space_occurance , grammar_mistakes, grammatical_indices = count_multiple_spaces(summary)
    print("count_double_space_occurance", count_double_space_occurance)
    print("Grammar Mistakes::", grammar_mistakes)
    nlp = spacy.load('en_core_web_sm')
    # print(nlp)
    doc = nlp(summary)
    num_errors = 0
    num_errors = count_double_space_occurance
    errors = []
    score = 2.0
    words_with_consonant_sound = ["Herb", "Honor", "Honest", "Unicorn", "European", "Unique", "Utensil", "Oven", "One", "Island", "Umbrella", "Urn", "Urge", "Urchin", "Awe", "Aye", "Aim", "Ark", "Ear", "Eagle", "Earn", "Earthen", "Early", "Earnest", "Eat", "Eel", "Eerie", "Eve", "Evil", "Eye", "Oil", "Oily", "Object", "Obstacle", "Occasion", "Occur", "Ocean", "Octave", "Octopus", "Ogle", "Ohm", "Ointment", "Omen", "Onset", "Onto", "Opera", "Operate", "Opportunity", "Opt", "Optic", "Oracle", "Oral", "Orbit", "Order", "Oregano", "Organ", "Orient", "Origin", "Ounce", "Our", "Oust", "Outlaw", "Ovation", "Over", "Overt", "Owl", "Owner", "Ox", "Oxen", "Oxygen"]
    vowels_not_starting_with_vowels = ['hour', 'heir', 'honor', 'honest', 'hymn', 'honorarium', 'honorific', 'houri', 'euro', 'eunuch', 'ewer']
    ed_ing_words = ["bed", "red", "shed", "wed", "led", "zed", "ced", "ded", "ged", "jed", "ned", "ped", "ted", "yed", "creed", "feed", "deed", "seed", "speed", "steed", "need", "sheed", "weed", "beed", "geed", "heed", "keed", "leed", "meed", "reed", "teed", "breed", "greed", "heed", "keed", "leed", "meed", "reed", "seed", "speed", "steed", "bring", "king", "sing", "spring", "swing", "wing", "zing", "bling", "cling", "ding", "fling", "ging", "ling", "ming", "ping", "ring", "sling", "ting", "ving", "bing", "cing", "ding", "fing", "ging", "hing", "jing", "king", "ling", "ming", "ning", "ping", "qing", "ring", "sing", "ting", "ving", "wing", "xing", "ying", "zwing"]
    # doc=merge_appos_words(doc)


    # Words that end in 's' but aren't plural
    non_plural_words = [
        "physics", "mathematics", "news", "series", "species", "chess", "measles",
        "alms", "corps", "darts", "headquarters", "means", "odds", "pants", "scissors",
        "glasses", "pajamas", "billiards", "ethics", "economics", "gymnastics",
        "linguistics", "mechanics", "politics", "aerobics", "acoustics", "logistics",
        "molasses", "mumps", "athletics", "aesthetics", "calisthenics", "corpses",
        "matins", "narcotics", "paralysis", "works", "minutes",
        "civics", "statics", "dynamics", "metaphysics", "abrasives", "geophysics",
        "diabetes", "diarrhea", "analytics", "dynamics", "hydraulics", "pneumatics",
        "semantics", "tropics", "cosmetics", "econometrics", "astrophysics", "genesis",
        "sclerosis", "tinnitus", "statistics", "politics", "classics", "enhances", "enriches",
        "serious", "serios", "stems", "follows"
    
    ]


    # Define patterns for plural words after "only", "one", or "only one"
    # This time, we allow one or two words in between before checking for a plural word
    plural_check_patterns = [
        r"\bonly(?:\s+\w+){0,2}\s+(?P<plural>\w+s)\b",  # up to 2 words after 'only'
        r"\bone(?:\s+\w+){0,2}\s+(?P<plural>\w+s)\b",  # up to 2 words after 'one'
        r"\bonly\s+one(?:\s+\w+){0,2}\s+(?P<plural>\w+s)\b"  # up to 2 words after 'only one'
    ]

    # Array to hold words to check against
    # words_to_avoid_after_phrases = ["benefit"]

    # List of phrases to check for
    phrases_to_check = ["several", "a few", "a number of", "a bunch of", "a variety of", "a collection of", "a range of", "a set of", "an assortment of", "plenty of", "a plethora of", "a myriad of", "countless", "various", "dozens of", "scores of", "multiple", "a host of", "a galaxy of", "a wealth of", "multiple other", "a multitude of other", "innumerable other", "several other", "various other", "countless other", "numerous other", "many other", "ample other", "numerous", "many"]

    matches1 = re.finditer(r'\b(several|a few|a number of|a bunch of|a variety of|a collection of|a range of|a set of|an assortment of|plenty of|a plethora of|a myriad of|countless|various|dozens of|scores of|multiple|a host of|a galaxy of|multiple other|a multitude of other|innumerable other|several other|various other|countless other|numerous other|many other|ample other|numerous|many)\b', summary)
    print("Matches:::", matches1)

    for match in matches1:
        start_index = match.start(1)  # Get start index of the phrase
        end_index = match.end(1)  # Get end index of the phrase
        phrase = summary[start_index:end_index].strip()

        phrase_end_index = start_index - 1
        word_start_index = end_index + 1
        word_end_index = word_start_index
        
        # Find the word following the phrase
        while word_end_index < len(summary) and summary[word_end_index].isalpha():
            word_end_index += 1
        word = summary[word_start_index:word_end_index]

        # Check if the word or the next word ends with ''
        next_word_start_index = word_end_index + 1
        next_word_end_index = next_word_start_index
        while next_word_end_index < len(summary) and summary[next_word_end_index].isalpha():
            next_word_end_index += 1
        next_word = summary[next_word_start_index:next_word_end_index]

        if word.endswith('s') or next_word.endswith('s') or word in stopwords or word in non_plural_words:
            continue

        # Append the error message, phrase, and indices to respective arrays
        errors.append(f"The word '{word}' should end with '' following the phrase '{phrase}'")
        grammar_mistakes.append(word)
        grammatical_indices.append((word_start_index, word_end_index, f"The word '{word}' should be plural following the phrase '{phrase}'"))




    # Helper function to check if a word is plural
    def is_plural(word):
        return word.endswith('s') and word not in non_plural_words and word not in stopwords


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


    # Matches sequences where the same punctuation mark repeats, allowing for optional spaces
    punctuation_matches = re.finditer(r'([^\w\s])(\s*\1)+', summary)
    for match in punctuation_matches:
        start_index = match.start(0)
        end_index = match.end(0)
        num_errors += 1
        errors.append("Repeated punctuation marks")
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append((start_index, end_index, "Repeated punctuation marks"))



    # This captures the full word that follows the full stop
    matches = re.finditer(r'\.(\w+)', summary)  # '.' followed by a word character(s)
    for match in matches:
        start_index = match.start()  # Position of the full stop
        end_index = match.end()  # Position of the end of the following word
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append((start_index, end_index,"No space after period"))
        num_errors += 1
        errors.append("No space after period")


    # Check for plural word after 'only', 'one', or 'only one' and not a stopword
    for pattern in plural_check_patterns:
        plural_matches = re.finditer(pattern, summary)
        for match in plural_matches:
            start_index = match.start('plural')
            end_index = match.end('plural')
            word = summary[start_index:end_index]
            
            if is_plural(word):
                num_errors += 1
                errors.append("Plural word after 'only', 'one', or 'only one'")
                grammar_mistakes.append(word)
                grammatical_indices.append((start_index, end_index, "Plural word after 'only', 'one', or 'only one'"))


    # Define the array of accepted repeated words
    allowed_repeated_words = [
    "had had", "that that", "the the", "is is", "it it", "do do", "you you", "are are",
    "was was", "will will", "would would", "if if", "on on", "at at", "in in", "has has",
    "to to", "from from", "as as", "by by", "he he", "we we", "they they", "go go", "no no",
    "why why", "how how"]

    # Compile the pattern to match repeated words or repeated pairs of words
    pattern = re.compile(r'\b(\w+)\b\s+\1\b|\b(\w+\s+\w+)\b\s+\2\b')


    # Check for repeated words or repeated pairs of words
    matches = re.finditer(pattern, summary)
    for match in matches:
        repeated_word = match.group(0).lower()  # get the repeated word
        if repeated_word not in allowed_repeated_words:  # if not in allowed list
            start_index = match.start(0)
            end_index = match.end(0)
            num_errors += 1
            errors.append("Repeated word")
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index, "Repeated word"))




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
    

    # Check for ' .' instead of '.'
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

    # Check for words not starting with a capital letter after a period
    period_indices = [i for i, token in enumerate(doc) if token.text == '.']
    for period_index in period_indices:
        # Check for text right after the period
        if period_index + 1 < len(doc):
            next_token = doc[period_index + 1]
            if next_token.is_alpha and not next_token.text[0].isupper():
                num_errors += 1
                errors.append("Word after period doesn't start with a capital letter")
                # Calculate the start index from the period token
                period_token = doc[period_index]
                start_index = period_token.idx
                
                # Calculate the end index based on the next token (the word)
                end_index = next_token.idx + len(next_token.text)
                
                # Append the segment from the period to the lowercase word
                grammar_mistakes.append(doc.text[start_index:end_index])
                grammatical_indices.append((start_index, end_index,"Word after period doesn't start with a capital letter"))



    # Check for words not starting with a capital letter after a period
    period_indices = [i for i, char in enumerate(summary) if char == '.']
    # Loop through all periods to check the following word
    for period_index in period_indices:
        # Check if there's a word after the period
        if period_index + 1 < len(summary) and summary[period_index + 1].isalpha():
            # Check if the first letter of the word is lowercase
            next_char = summary[period_index + 1]
            if not next_char.isupper():
                # Find the complete word following the period
                match = re.search(r'\.\s*([a-z]+)', summary[period_index:])
                
                if match:
                    # Add the word that is not capitalized and its indices
                    num_errors += 1
                    errors.append("Word after period doesn't start with a capital letter")
                    
                    # Start index from the period
                    start_index = period_index
                    # End index from the length of the word after the period
                    end_index = period_index + match.end(1)
                    
                    # Store the segment including the period and non-capitalized word
                    grammar_mistakes.append(summary[start_index:end_index])
                    grammatical_indices.append((start_index, end_index, "Word after period doesn't start with a capital letter"))



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
                        grammar_mistakes.append(word[0], )
                        grammatical_indices.append((comma_index, comma_index + 1 + len(word[0]),"Missing space after comma"))





    # Split the text into paragraphs
    paragraphs = summary.split('\n')

    # Iterate over each paragraph
    for paragraph in paragraphs:
        if paragraph.strip():
            if paragraph[0].islower():
                num_errors += 1
                errors.append("Paragraph doesn't start with a capital letter")
                # Add the first word of the paragraph causing the error to grammar_mistakes array
                first_word_match = re.search(r'\b([a-zA-Z]+)\b', paragraph)
                if first_word_match:
                    first_word = first_word_match.group(1)
                    start_index = summary.find(paragraph) + first_word_match.start(1)
                    end_index = summary.find(paragraph) + first_word_match.end(1)
                    grammar_mistakes.append((first_word))
                    grammatical_indices.append((start_index, end_index, "Paragraph doesn't start with a capital letter"))


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

        mistake_start_idx = token.idx
        mistake_end_idx = token.idx + len(token.text)

        # Get the token's start index in the text
        token_start = token.idx

        # Check if the token is at the beginning of a sentence or paragraph
        is_first_word = any(sb == token_start for sb in all_boundaries)

        # If the word is "i", skip this check
        if token.text.lower() == 'i':
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
        if token.tag_ != 'NNP' and token.text[0].isupper() and not in_brackets and not in_quotes and not is_first_word_in_sentence and not is_first_word and not is_first_word_in_doc:
            if token.text in ['Latin','X-ray','X']:
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
            grammatical_indices.append((mistake_start_idx, mistake_end_idx),f"Lowercase proper noun: '{token.text}'")


        # Rule 2: Use of 'whom' instead of 'who' in subject position
        if token.text.lower() == 'whom' and (token.dep_ == 'nsubj' or token.dep_ == 'nsubjpass'):
            num_errors += 1
            errors.append("Use of 'whom' instead of 'who' in subject position")
            grammar_mistakes.append(('whom'))
            grammatical_indices.append((mistake_start_idx, mistake_end_idx), "Use of 'whom' instead of 'who' in subject position")


        # Rule 3: Incorrect use of apostrophes ('s vs. s')
        if token.text == "'s":
            previous_token = token.nbor(-1)
            
            if token.head.pos_ in ['NUM'] and token.head.text !='one':
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for numbers.")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx),"Incorrect use of apostrophe ('s) for numbers.")

            # Check if the token is not attached to a noun
            elif token.head.pos_ not in ['NOUN', 'PROPN', 'PRON', 'VERB', 'NUM', 'AUX']:
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx),"Incorrect use of apostrophe ('s) for non-nouns")

            # Check if the token is attached to a proper noun
            elif token.head.tag_ == 'NNP' and not token.dep_ in ['poss','case']:
                print("TOKEN DEP::", token.dep_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for proper nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx),"Incorrect use of apostrophe ('s) for proper nouns")


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
                grammatical_indices.append((mistake_start_idx, mistake_end_idx),"Conjunction error: Incorrect use of conjunction")


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
        

        # Rule 7: Check for punctuation mistakes
        if token.pos_ == 'PUNCT':
            if token.text not in ['.', ',', '!', '?', ':', ';', '“', '”', '‘', '’', '—', '–', '-', '"', "'", '(', ')', '[', ']', '{', '}', '/', '\\', '_', '*', '&', '@', '#', '$', '%', '^', '<', '>', '|', '`', '~', '+', '=', '..', '...', '¿', '¡']:
                num_errors += 1
                errors.append(f"Unexpected punctuation: '{token.text}'")
                grammar_mistakes.append((token.text))
                grammatical_indices.append((mistake_start_idx, mistake_end_idx, f"Unexpected punctuation: '{token.text}'"))
            
    # Extract the ending indices
    ending_indices = [indices[1] for indices in grammatical_indices]

    # Count the number of duplicates
    num_duplicates = len(ending_indices) - len(set(ending_indices))

    # Keep only the unique ending indices
    unique_indices = list(set(ending_indices))

    # Remove the duplicates and keep one instance
    unique_grammatical_indices = []
    for indices in grammatical_indices:
        if indices[1] in unique_indices:
            unique_grammatical_indices.append(indices)
            unique_indices.remove(indices[1])

    num_errors = len(unique_grammatical_indices)

    if num_errors > 0:
        print("Grammatical errors detected:")
        for error in errors:
            print("-", error)

    
    if num_errors == 0:
        pass
    elif num_errors == 1:
        score -=0.5
    elif num_errors == 2:
        score -=1.0
    elif num_errors == 3:
        score -= 1.5
    else:
        score = 0.0


    grammatical_indices= unique_grammatical_indices

    return score , grammar_mistakes, grammatical_indices
    




def calculate_vocab_range_score_eassy(essay_text, form_score, grammar_score):

    vocab_score = 2.0
    if grammar_score == 0.0:
        print("BECAUSE GRAMMAR SCORE IS 0, I AM HERE.")
        vocab_score-=1.0
    # Tokenize the essay into words (you might need to preprocess the text further)
    words = essay_text.lower().split()

    # print("FORM SCORE:", form_score)
    
    # Calculate the total number of unique words
    unique_words = set(words)
    total_unique_words = len(unique_words)

    # Define the vocabulary range thresholds
    low_threshold = 0.2 * total_unique_words
    high_threshold = 0.8 * total_unique_words

    if form_score == 0.0:
        return 0.0
    else:
        if total_unique_words <= low_threshold:
            return 0.0
        elif total_unique_words >= high_threshold:
            score = min(vocab_score, form_score)
            print("HELLO 1")  # Ensure vocab score doesn't exceed form score
        else:
            vocab_score = (total_unique_words - low_threshold) / (high_threshold - low_threshold) * 2
            score = min(round(vocab_score, 2), form_score)  # Ensure vocab score doesn't exceed form score
            print("HELLO 2")
        return score



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
                if any(start_index == g_start or end_index == g_end for g_start, g_end, g_dummy in grammatical_indices):
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
       
      
def contains_only_bullet_points(text):
    lines = text.split('\n')
    for line in lines:
        # Check if the line is not empty and doesn't start with a bullet point
        if line.strip() and not line.strip().startswith(('*', '-', '•', '‣', '◦', '⁃')):
            return False
    return True
   

    





def calculate_form_score_essay(essay):
    form_score=2.0
    check_case=essay.isupper()
    punc_check=any(char in string.punctuation for char in essay)
    bullet_check=contains_only_bullet_points(essay)
    if check_case==False and punc_check==True and bullet_check==False :
        print("Essay has no issue in form")
        word_count = len(essay.split())
        if word_count>=200 and word_count<=300:
            print("Essay is between 200-300")
            return form_score
        elif word_count>=120 and word_count<=199:
            print("Essay is between 120-199")
            form_score-=1.0
            return form_score
        elif word_count>=301 and word_count<=380:
            print("Essay is between 301-380")
            form_score-=1.0
            return form_score
        else:
            return 0.0
    else:
        return 0.0
    









def calculate_general_linguistic_range_score(essay, form_score):
    words = word_tokenize(essay.lower())
    unique_words = set(words)
    linguistic_range_score = 2 * len(unique_words) / len(words)  # Scale adjustment

    print("Linguistic::",linguistic_range_score)
    
    
    # print("Linguistic::",linguistic_range_score)
    score= min(linguistic_range_score, 2.0)  # Ensure the score does not exceed 2
    # print("FORM SCORE:", form_score)
    print("Linguistic::",score)
    
    if form_score == 0.0:
        return 0.0
    
    
    else:
        if score ==0:
            res= 0.0
        elif score >0 and score<=0.2:
            res= 0.75
        elif score >0.2 and score<=0.4:
            res= 1.0
        elif score >0.4 and score<=0.6:
            res= 1.5
        elif score >0.6 and score<=0.8:
            res= 1.75
        else:
            res=2.0
    

    print("Res::", res)
    lingres = min(res, form_score)

    return lingres





def calculate_development_structure_coherence_score(essay):
    essay=essay.replace("\n\n","\n")
    paragraphs = essay.split('\n')
    cleaned_list = [s.strip() for s in paragraphs if s.strip()]
    num=len(cleaned_list)

    if num ==3 or num ==4 or num ==5:     #3,4,5      
        return 2.0
    elif  num ==2:
        return 1.0
    else:
        return 0.0


def temp_content_scoring(essay, question, major_aspect, minor_aspect):
    content_score = 3.0
    temp=essay  
    main_string_no_punctuation_lower=remove_punctuation_and_lower(temp)
    question_no_punctuation_lower=remove_punctuation_and_lower(question)
    
    # Count the occurrences of the question in the main string
    question_count = main_string_no_punctuation_lower.count(question_no_punctuation_lower)
 
    if question_count == 1:
        content_score -= 1.0
    elif question_count == 2:
        content_score -= 2.0
    elif question_count >= 3:
        return 0.0 

    conditions = {
        "example": "example" in question_no_punctuation_lower or "examples" in question_no_punctuation_lower,
        "advantages_disadvantages": ("advantages" in question_no_punctuation_lower) or ("disadvantages" in question_no_punctuation_lower),
        "agree_disagree": ("agree" in question_no_punctuation_lower) or ("disagree" in question_no_punctuation_lower),
        "positive_negative": ("positive" in question_no_punctuation_lower) or ("negative" in question_no_punctuation_lower)
    }

    if(conditions["example"]):
        if('example' not in main_string_no_punctuation_lower and 'examples' not in main_string_no_punctuation_lower):
            content_score -= 1.0
    if(conditions["advantages_disadvantages"]):
        if('advantages' not in main_string_no_punctuation_lower and 'disadvantages' not in main_string_no_punctuation_lower):
            content_score -= 1.0
    if(conditions["agree_disagree"]):
        if('agree' not in main_string_no_punctuation_lower and 'disagree' not in main_string_no_punctuation_lower):
            content_score -= 1.0
    if(conditions["positive_negative"]):
        if('positive' not in main_string_no_punctuation_lower and 'negative' not in main_string_no_punctuation_lower):
            content_score -= 1.0                        

    parts = essay.split("\n")
    result = 0
    minor_minus_mark = 0
    is_there_minor = False
    major_minus_mark = 0
    is_there_major = False

    if len(parts) == 1:
        result = {'Intro': parts[0].lower()}
        content_score -= 1.0
        for minor in minor_aspect:
          if(not isinstance(minor, list)):
            if minor.lower() not in result['Intro']:
              minor_minus_mark += 0.25
            else:
              is_there_minor = True
          else:
            tmp_minor_mark = 0.25 
            for item in minor:
              if item.lower() in result['Intro']:
                tmp_minor_mark = 0
                is_there_minor = True
            minor_minus_mark += tmp_minor_mark               

        for major in major_aspect:            
          if(not isinstance(major, list)):
            if major.lower() not in result['Intro']:
              major_minus_mark += 1
            else:
              is_there_major = True
          else:
            tmp_major_mark = 1 
            for item in major:
              if item.lower() in result['Intro']:
                tmp_major_mark = 0
                is_there_major = True
            major_minus_mark += tmp_major_mark

    elif len(parts) == 2:
        result = {'Intro': parts[0].lower(), 'para': parts[1].lower()}
        content_score -= 1.0
        for minor in minor_aspect:
          if(not isinstance(minor, list)):          
            if minor.lower() not in result['Intro'] or minor.lower() not in result['para']:
              minor_minus_mark += 0.25
            else:
              is_there_minor = True            
          else:
            tmp_minor_mark = 0.25 
            for item in minor:
              if item.lower() in result['Intro'] and item.lower() in result['para']:
                tmp_minor_mark = 0
                is_there_minor = True
            minor_minus_mark += tmp_minor_mark

        for major in major_aspect:            
          if(not isinstance(major, list)):
            if major.lower() not in result['Intro'] or major.lower() not in result['para']:
              major_minus_mark += 1
            else:
              is_there_major = True
          else:
            tmp_major_mark = 1 
            for item in major:
              if item.lower() in result['Intro'] and item.lower() in result['para']:
                tmp_major_mark = 0
                is_there_major = True
            major_minus_mark += tmp_major_mark

    else:
        result = {
            'Intro': parts[0].lower(),
            'para': "\n".join(parts[1:-1]).lower(),  # Middle part(s)
            'conclusion': parts[-1].lower()
        }
        for minor in minor_aspect:
          if(not isinstance(minor, list)):          
            if minor.lower() not in result['Intro'] or minor.lower() not in result['para'] or minor.lower() not in result['conclusion']:
              minor_minus_mark += 0.25        
            else:
              is_there_minor = True
          else:
            tmp_minor_mark = 0.25 
            for item in minor:
              if item.lower() in result['Intro'] and item.lower() in result['para'] and item.lower() in result['conclusion']:
                tmp_minor_mark = 0
                is_there_minor = True
            minor_minus_mark += tmp_minor_mark

        for major in major_aspect:            
          if(not isinstance(major, list)):
            if major.lower() not in result['Intro'] or major.lower() not in result['para'] or major.lower() not in result['conclusion']:
              major_minus_mark += 1
            else:
              is_there_major = True
          else:
            tmp_major_mark = 1 
            for item in major:
              if item.lower() in result['Intro'] and item.lower() in result['para'] and item.lower() in result['conclusion']:
                tmp_major_mark = 0
                is_there_major = True
            major_minus_mark += tmp_major_mark


    if not is_there_minor or minor_minus_mark>1:
      minor_minus_mark = 1

    if not is_there_major or major_minus_mark>2:
      major_minus_mark = 2

    content_score -= minor_minus_mark
    content_score -= major_minus_mark

    if(content_score<0):
      content_score = 0

    return content_score


def score_essay(essay,question,major_aspect,minor_aspect,accent):
    # content_score = calculate_content_score(essay,question,major_aspect,minor_aspect)
    content_score = temp_content_scoring(essay,question,major_aspect,minor_aspect)
    # grammar_score , grammar_mistakes , grammatical_indices = calculate_grammar_score_essay(essay)
    grammar_score = 1
    grammar_mistakes = []
    grammatical_indices = []

    spelling_score, correct_words, misspelled_indices = calculate_spelling_score(essay, accent, grammatical_indices)
    form_score = calculate_form_score_essay(essay)
    vocab_range_score = calculate_vocab_range_score_eassy(essay, form_score, grammar_score)
    general_linguistic_range_score = calculate_general_linguistic_range_score(essay, form_score)
    development_structure_coherence_score = calculate_development_structure_coherence_score(essay)
    if form_score==0 or content_score==0:
        content_score = 0
        grammar_score = 0
        vocab_range_score = 0
        spelling_score=0
        correct_words = 0
        form_score = 0
        general_linguistic_range_score = 0
        development_structure_coherence_score = 0
    comments = set_essay_comments(content_score , grammar_score , vocab_range_score ,spelling_score , form_score , general_linguistic_range_score , development_structure_coherence_score)

    total_score = content_score + grammar_score + vocab_range_score + spelling_score + form_score + general_linguistic_range_score + development_structure_coherence_score
    total_score=round(total_score,1)
    updated_score=round(total_score * 4) / 4
      
    return content_score, grammar_score, vocab_range_score, spelling_score, form_score, general_linguistic_range_score, development_structure_coherence_score, updated_score,correct_words,comments, grammar_mistakes, misspelled_indices, grammatical_indices
