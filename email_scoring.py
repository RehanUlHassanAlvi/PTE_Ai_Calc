import nltk
from nltk.tokenize import word_tokenize
import spacy
import re
from constants import WORD_LIST
from collections import Counter
import string
import enchant
from comments.email_comments import set_email_comments
from helper_functions.email_content_score_helper import (
    remove_punctuation_and_lower,
    detect_values_with_spaces,
    stem_words,
    generate_word_status_for_major_dict,
    generate_word_status_for_minor_dict,
    generate_word_status_dict_for_major_and_minor_for_less_para,
    scoring,
    generate_multiword_status_for_major_dict,
    generate_multiword_status_for_minor_dict,
    generate_all_words_aspects_dict,
    stem_words2,
)
from helper_functions.essay_grammer_score_helper import count_multiple_spaces

# nltk.download('stopwords', download_dir='nltk_data/')
# nltk.download('vader_lexicon', download_dir='nltk_data/')
nltk.data.path.append("nltk_data/")
nltk.download("stopwords")
# nltk.download('vader_lexicon')
from nltk.corpus import stopwords

# nltk.download('stopwords')

stopwords = set(stopwords.words("english"))
# print("STOPWORDS:::", stopwords)


def update_dict_recursively(original_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict):
            original_dict[key] = update_dict_recursively(
                original_dict.get(key, {}), value
            )
        elif isinstance(value, list):
            original_dict[key] = value
        else:
            original_dict[key] = value
    return original_dict


def extract_capital_words(text):
    # Regex pattern for words starting with a capital letter
    capital_words_pattern = re.compile(r"\b[A-Z][a-z]*\b")

    # List of prefixes that might precede capitalized words
    name_prefixes = ["Mr", "Mrs", "Miss", "Dr", "Sir"]

    # Extract all capitalized words
    capitalized_words = capital_words_pattern.findall(text)

    # Extract words that follow the specified prefixes
    words_after_prefixes = []
    words = text.split()  # Split the text into words
    for i, word in enumerate(words):
        if word in name_prefixes and i + 1 < len(words):
            # The word after the prefix
            words_after_prefixes.append(words[i + 1])

    # Combine both lists and remove duplicates
    combined_words = list(set(capitalized_words + words_after_prefixes))

    return combined_words


def calculate_content_score(email, question, major_aspect, minor_aspect):
    content_score = 3.0
    temp = email

    copy_major_aspect = major_aspect[:]

    copy_minor_aspect = minor_aspect[:]

    main_string_no_punctuation_lower = remove_punctuation_and_lower(temp)
    question_no_punctuation_lower = remove_punctuation_and_lower(question)

    print("QUESTION::", question_no_punctuation_lower)
    # Count the occurrences of the question in the main string
    question_count = main_string_no_punctuation_lower.count(
        question_no_punctuation_lower
    )

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
        "advantages_disadvantages": ("advantages" in question_no_punctuation_lower)
        or ("disadvantages" in question_no_punctuation_lower),
        "agree_disagree": ("agree" in question_no_punctuation_lower)
        or ("disagree" in question_no_punctuation_lower),
        "positive_negative": ("positive" in question_no_punctuation_lower)
        or ("negative" in question_no_punctuation_lower),
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
                elif conditions["advantages_disadvantages"] and word in [
                    "advantages",
                    "disadvantages",
                ]:
                    element.remove(word)
                elif conditions["agree_disagree"] and word in ["agree", "disagree"]:
                    element.remove(word)
                elif conditions["positive_negative"] and word in [
                    "positive",
                    "negative",
                ]:
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
            elif conditions["advantages_disadvantages"] and element in [
                "advantages",
                "disadvantages",
            ]:
                minor_aspect.remove(element)
            elif conditions["agree_disagree"] and element in ["agree", "disagree"]:
                minor_aspect.remove(element)
            elif conditions["positive_negative"] and element in [
                "positive",
                "negative",
            ]:
                minor_aspect.remove(element)
            else:
                i += 1

    # Print the updated minor aspects
    print("Updated Minor Aspects:", minor_aspect)

    major_aspect_with_spaces = detect_values_with_spaces(major_aspect)
    minor_aspect_with_spaces = detect_values_with_spaces(minor_aspect)

    print("MINOR ASPECTS", minor_aspect_with_spaces)

    for value in major_aspect_with_spaces:
        major_aspect.remove(value)

    for value in minor_aspect_with_spaces:
        minor_aspect.remove(value)

    stemmed_major_aspect = stem_words(major_aspect)
    stemmed_minor_aspect = stem_words2(minor_aspect)

    print(stemmed_minor_aspect)

    email = email.replace("\n\n", "\n")
    # email = email.replace(" .", " ")
    paragraphs = email.split("\n")
    paragraphs = [s for s in paragraphs if s != ""]

    print("total paragraphs: ", len(paragraphs))

    if len(paragraphs) >= 3:
        body_values = paragraphs[1:-1]
        main_body = " ".join(body_values)

        main_body = remove_punctuation_and_lower(main_body)

        # print(content_score)
        main_body_words = main_body.split()

        print("MAIN BODY:::::", main_body_words)

        multi_word_major_aspect_dict = generate_multiword_status_for_major_dict(
            major_aspect_with_spaces, main_body
        )
        multi_word_minor_aspect_dict = generate_multiword_status_for_minor_dict(
            minor_aspect_with_spaces, main_body
        )

        # print(minor_aspect_with_spaces)
        stemmed_main_body_words = stem_words(main_body_words)

        main_body_major_aspect_counts = Counter(stemmed_main_body_words)
        print("MAIN BODY MAJOR ASPECTS COUNT:::", main_body_major_aspect_counts)

        main_body_minor_aspect_counts = Counter(stemmed_main_body_words)

        major_aspects_status_dict = generate_word_status_for_major_dict(
            stemmed_major_aspect, main_body_major_aspect_counts
        )
        print("MAJOR ASPECTS STATUS DICT:::", major_aspects_status_dict)

        minor_aspects_status_dict = generate_word_status_for_minor_dict(
            stemmed_minor_aspect, main_body_minor_aspect_counts
        )

        major_aspects_status_dict.update(multi_word_major_aspect_dict)
        print("MULTI WORD MAJOR ASPECTS STATUS DICT:::", major_aspects_status_dict)

        minor_aspects_status_dict = update_dict_recursively(
            minor_aspects_status_dict, multi_word_minor_aspect_dict
        )

        # print("MINOR ASPECTS AFTER PREPROCESSING",minor_aspects_status_dict)

        # Check if the keyword "example" is in the question
        example_in_question = "example" in question_no_punctuation_lower

        # Check if "advantages" or "disadvantages" is in the question
        advantages_or_disadvantages_in_question = (
            "advantages" in question_no_punctuation_lower
        ) or ("disadvantages" in question_no_punctuation_lower)

        # Check if "agree" or "disagree" is in the question
        agree_or_disagree_in_question = ("agree" in question_no_punctuation_lower) or (
            "disagree" in question_no_punctuation_lower
        )

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
            if ("advantages" in main_string_no_punctuation_lower) or (
                "disadvantages" in main_string_no_punctuation_lower
            ):
                print("Advantages or disadvantages mentioned in the body")
            else:
                print("Advantages or disadvantages not mentioned in the body")
                # Deduct content score if neither "advantages" nor "disadvantages" is mentioned in the body
                content_score -= 1.0

        if agree_or_disagree_in_question:
            # If "agree" or "disagree" is in the question, check if either is mentioned in the body
            if ("agree" in main_string_no_punctuation_lower) or (
                "disagree" in main_string_no_punctuation_lower
            ):
                print("Agree or disagree mentioned in the body")
            else:
                print("Agree or disagree not mentioned in the body")
                # Deduct content score if neither "agree" nor "disagree" is mentioned in the body
                content_score -= 1.0

        # Check if "positive" or "negative" is in the question
        positive_or_negative_in_question = (
            "positive" in question_no_punctuation_lower
        ) or ("negative" in question_no_punctuation_lower)

        if positive_or_negative_in_question:
            # If "positive" or "negative" is in the question, check if either is mentioned in the body
            if ("positive" in main_string_no_punctuation_lower) or (
                "negative" in main_string_no_punctuation_lower
            ):
                print("Positive or negative mentioned in the body")
            else:
                print("Positive or negative not mentioned in the body")
                # Deduct content score if neither "positive" nor "negative" is mentioned in the body
                content_score -= 1.0

        score = scoring(
            major_aspects_status_dict,
            minor_aspects_status_dict,
            len(paragraphs),
            content_score,
        )
        # print("content score: ",score)

    else:
        cscore = 3.0
        email_words = email.split()
        stemmed_email_words = stem_words(email_words)
        multi_word_major_aspect_dict, multi_word_minor_aspect_dict = (
            generate_all_words_aspects_dict(
                major_aspect_with_spaces, minor_aspect_with_spaces, email_words
            )
        )

        major_aspects_status_dict, minor_aspects_status_dict = (
            generate_word_status_dict_for_major_and_minor_for_less_para(
                stemmed_major_aspect, stemmed_minor_aspect, stemmed_email_words
            )
        )

        major_aspects_status_dict.update(multi_word_major_aspect_dict)
        minor_aspects_status_dict.update(multi_word_minor_aspect_dict)

        # Check if the keyword "example" is in the question
        example_in_question = "example" in question_no_punctuation_lower

        # Check if "advantages" or "disadvantages" is in the question
        advantages_or_disadvantages_in_question = (
            "advantages" in question_no_punctuation_lower
        ) or ("disadvantages" in question_no_punctuation_lower)

        # Check if "agree" or "disagree" is in the question
        agree_or_disagree_in_question = ("agree" in question_no_punctuation_lower) or (
            "disagree" in question_no_punctuation_lower
        )

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
            if ("advantages" in main_string_no_punctuation_lower) or (
                "disadvantages" in main_string_no_punctuation_lower
            ):
                print("Advantages or disadvantages mentioned in the body")
            else:
                print("Advantages or disadvantages not mentioned in the body")
                # Deduct content score if neither "advantages" nor "disadvantages" is mentioned in the body
                cscore -= 1.0

        if agree_or_disagree_in_question:
            # If "agree" or "disagree" is in the question, check if either is mentioned in the body
            if ("agree" in main_string_no_punctuation_lower) or (
                "disagree" in main_string_no_punctuation_lower
            ):
                print("Agree or disagree mentioned in the body")
            else:
                print("Agree or disagree not mentioned in the body")
                # Deduct content score if neither "agree" nor "disagree" is mentioned in the body
                print("CCCCCCCCCCC", cscore)
                cscore -= 1.0
                print("CCCCCCCCCCC", cscore)

        # Check if "positive" or "negative" is in the question
        positive_or_negative_in_question = (
            "positive" in question_no_punctuation_lower
        ) or ("negative" in question_no_punctuation_lower)

        if positive_or_negative_in_question:
            # If "positive" or "negative" is in the question, check if either is mentioned in the body
            if ("positive" in main_string_no_punctuation_lower) or (
                "negative" in main_string_no_punctuation_lower
            ):
                print("Positive or negative mentioned in the body")
            else:
                print("Positive or negative not mentioned in the body")
                # Deduct content score if neither "positive" nor "negative" is mentioned in the body
                cscore -= 1.0

        score = scoring(
            major_aspects_status_dict,
            minor_aspects_status_dict,
            len(paragraphs),
            cscore,
        )
        print("content score: ", score)

    return score


def calculate_grammar_score_email(summary):
    print(summary)
    grammatical_indices = []
    count_double_space_occurance, grammar_mistakes, grammatical_indices = (
        count_multiple_spaces(summary)
    )
    print("count_double_space_occurance", count_double_space_occurance)
    print("Grammar Mistakes::", grammar_mistakes)
    nlp = spacy.load("en_core_web_sm")
    # print(nlp)
    doc = nlp(summary)
    num_errors = 0
    num_errors = count_double_space_occurance
    errors = []
    score = 2.0
    words_with_consonant_sound = [
        "Herb",
        "Honor",
        "Honest",
        "Unicorn",
        "European",
        "Unique",
        "Utensil",
        "Oven",
        "One",
        "Island",
        "Umbrella",
        "Urn",
        "Urge",
        "Urchin",
        "Awe",
        "Aye",
        "Aim",
        "Ark",
        "Ear",
        "Eagle",
        "Earn",
        "Earthen",
        "Early",
        "Earnest",
        "Eat",
        "Eel",
        "Eerie",
        "Eve",
        "Evil",
        "Eye",
        "Oil",
        "Oily",
        "Object",
        "Obstacle",
        "Occasion",
        "Occur",
        "Ocean",
        "Octave",
        "Octopus",
        "Ogle",
        "Ohm",
        "Ointment",
        "Omen",
        "Onset",
        "Onto",
        "Opera",
        "Operate",
        "Opportunity",
        "Opt",
        "Optic",
        "Oracle",
        "Oral",
        "Orbit",
        "Order",
        "Oregano",
        "Organ",
        "Orient",
        "Origin",
        "Ounce",
        "Our",
        "Oust",
        "Outlaw",
        "Ovation",
        "Over",
        "Overt",
        "Owl",
        "Owner",
        "Ox",
        "Oxen",
        "Oxygen",
    ]
    vowels_not_starting_with_vowels = [
        "hour",
        "heir",
        "honor",
        "honest",
        "hymn",
        "honorarium",
        "honorific",
        "houri",
        "euro",
        "eunuch",
        "ewer",
    ]
    ed_ing_words = [
        "bed",
        "red",
        "shed",
        "wed",
        "led",
        "zed",
        "ced",
        "ded",
        "ged",
        "jed",
        "ned",
        "ped",
        "ted",
        "yed",
        "creed",
        "feed",
        "deed",
        "seed",
        "speed",
        "steed",
        "need",
        "sheed",
        "weed",
        "beed",
        "geed",
        "heed",
        "keed",
        "leed",
        "meed",
        "reed",
        "teed",
        "breed",
        "greed",
        "heed",
        "keed",
        "leed",
        "meed",
        "reed",
        "seed",
        "speed",
        "steed",
        "bring",
        "king",
        "sing",
        "spring",
        "swing",
        "wing",
        "zing",
        "bling",
        "cling",
        "ding",
        "fling",
        "ging",
        "ling",
        "ming",
        "ping",
        "ring",
        "sling",
        "ting",
        "ving",
        "bing",
        "cing",
        "ding",
        "fing",
        "ging",
        "hing",
        "jing",
        "king",
        "ling",
        "ming",
        "ning",
        "ping",
        "qing",
        "ring",
        "sing",
        "ting",
        "ving",
        "wing",
        "xing",
        "ying",
        "zwing",
    ]
    # doc=merge_appos_words(doc)

    # Check for ' .' instead of '.'
    if " ." in summary:
        num_errors += summary.count(" .")
        errors.append("Space before period")
        # Add words causing the error to grammar_mistakes array
        matches = re.finditer(r"(\w+) \.", summary)
        for match in matches:
            start_index = match.start()
            end_index = match.end()
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index, "Space before period"))

    # Check for continuous occurrences of the same punctuation mark
    # Matches sequences where the same punctuation mark repeats, allowing for optional spaces
    punctuation_matches = re.finditer(r"([^\w\s])(\s*\1)+", summary)
    for match in punctuation_matches:
        start_index = match.start(0)
        end_index = match.end(0)
        num_errors += 1
        errors.append("Repeated punctuation marks")
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append(
            (start_index, end_index, "Repeated punctuation marks")
        )

    # Check for no space after a full stop, except the last full stop
    # This captures the full word that follows the full stop
    matches = re.finditer(r"\.(\w+)", summary)  # '.' followed by a word character(s)
    for match in matches:
        start_index = match.start()  # Position of the full stop
        end_index = match.end()  # Position of the end of the following word
        grammar_mistakes.append(summary[start_index:end_index])
        grammatical_indices.append((start_index, end_index, "No space after period"))
        num_errors += 1
        errors.append("No space after period")

    # Define the array of accepted repeated words
    allowed_repeated_words = [
        "had had",
        "that that",
        "the the",
        "is is",
        "it it",
        "do do",
        "you you",
        "are are",
        "was was",
        "will will",
        "would would",
        "if if",
        "on on",
        "at at",
        "in in",
        "has has",
        "to to",
        "from from",
        "as as",
        "by by",
        "he he",
        "we we",
        "they they",
        "go go",
        "no no",
        "why why",
        "how how",
    ]

    # Check for repeated words (same word occurring twice continuously)
    matches = re.finditer(r"\b(\w+)\b\s+\1\b", summary)
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
    word_to_check = "i"
    if word_to_check.lower() in summary:
        matches = re.finditer(r"\b" + re.escape(word_to_check) + r"\b", summary)
        for match in matches:
            if match.group(0) == word_to_check.lower():
                start_index = match.start(0)
                end_index = match.end(0)
                num_errors += 1
                errors.append(f"Word '{word_to_check}' appears in lowercase")
                grammar_mistakes.append(summary[start_index:end_index])
                grammatical_indices.append(
                    (
                        start_index,
                        end_index,
                        f"Word '{word_to_check}' appears in lowercase",
                    )
                )

    # Check for ' .' instead of '.'
    if " ," in summary:
        num_errors += summary.count(" ,")
        errors.append("Space before Comma")
        # Add words causing the error to grammar_mistakes array
        matches = re.finditer(r"(\w+) \,", summary)
        for match in matches:
            start_index = match.start(1)
            end_index = match.end(0)
            grammar_mistakes.append(summary[start_index:end_index])
            grammatical_indices.append((start_index, end_index, "Space before Comma"))

    # Words considered errors
    incorrect_words = ["fishes", "peoples", "leafs", "gooses", "shrimps"]

    # Check if any of these words appear in the summary
    for word in incorrect_words:
        if word in summary:
            num_errors += summary.count(word)
            errors.append(f"Incorrect word usage: {word}")
            # Find occurrences of the incorrect word in the summary
            matches = re.finditer(r"\b" + re.escape(word) + r"\b", summary)
            for match in matches:
                start_index = match.start()
                end_index = match.end()
                grammar_mistakes.append(summary[start_index:end_index])
                grammatical_indices.append(
                    (start_index, end_index, f"Incorrect word usage: {word}")
                )

    # Check for words not starting with a capital letter after a period
    period_indices = [i for i, token in enumerate(doc) if token.text == "."]
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
                grammatical_indices.append(
                    (
                        start_index,
                        end_index,
                        "Word after period doesn't start with a capital letter",
                    )
                )

    # Check for words not starting with a capital letter after a period
    period_indices = [i for i, char in enumerate(summary) if char == "."]
    # Loop through all periods to check the following word
    for period_index in period_indices:
        # Check if there's a word after the period
        if period_index + 1 < len(summary) and summary[period_index + 1].isalpha():
            # Check if the first letter of the word is lowercase
            next_char = summary[period_index + 1]
            if not next_char.isupper():
                # Find the complete word following the period
                match = re.search(r"\.\s*([a-z]+)", summary[period_index:])

                if match:
                    # Add the word that is not capitalized and its indices
                    num_errors += 1
                    errors.append(
                        "Word after period doesn't start with a capital letter"
                    )

                    # Start index from the period
                    start_index = period_index
                    # End index from the length of the word after the period
                    end_index = period_index + match.end(1)

                    # Store the segment including the period and non-capitalized word
                    grammar_mistakes.append(summary[start_index:end_index])
                    grammatical_indices.append(
                        (
                            start_index,
                            end_index,
                            "Word after period doesn't start with a capital letter",
                        )
                    )

    # Check for missing space after comma
    if "," in summary:
        comma_indices = [i for i, char in enumerate(summary) if char == ","]
        for comma_index in comma_indices:
            # Check if there's a character right after the comma
            if comma_index + 1 < len(summary):
                next_char = summary[comma_index + 1]
                # Ignore if the next character is a space or a special character
                if next_char != " " and not next_char.isalnum():
                    continue
                # Check for missing space only if the next character is alphanumeric
                if next_char != " ":
                    num_errors += 1
                    errors.append("Missing space after comma")
                    # Add the word causing the error to grammar_mistakes array
                    word = re.findall(r",\s*(\w+)", summary[comma_index:])
                    if word:
                        grammar_mistakes.append((word[0],))
                        grammatical_indices.append(
                            (
                                comma_index,
                                comma_index + 1 + len(word[0]),
                                "Missing space after comma",
                            )
                        )

    # Split the text into paragraphs
    paragraphs = summary.split("\n")

    # Iterate over each paragraph
    for paragraph in paragraphs:
        if paragraph.strip():
            if paragraph[0].islower():
                num_errors += 1
                errors.append("Paragraph doesn't start with a capital letter")
                # Add the first word of the paragraph causing the error to grammar_mistakes array
                first_word_match = re.search(r"\b([a-zA-Z]+)\b", paragraph)
                if first_word_match:
                    first_word = first_word_match.group(1)
                    start_index = summary.find(paragraph) + first_word_match.start(1)
                    end_index = summary.find(paragraph) + first_word_match.end(1)
                    grammar_mistakes.append((first_word))
                    grammatical_indices.append(
                        (
                            start_index,
                            end_index,
                            "Paragraph doesn't start with a capital letter",
                        )
                    )

    sentence_boundary_regex = re.compile(
        r"[.!?]\s"
    )  # regex to identify sentence boundaries
    paragraph_boundary_regex = re.compile(r"\n\s*")

    # Find all sentence boundaries
    sentence_boundaries = [m.end() for m in sentence_boundary_regex.finditer(doc.text)]

    # Find all paragraph boundaries
    paragraph_boundaries = [
        m.end() for m in paragraph_boundary_regex.finditer(doc.text)
    ]

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
        if token.text.lower() in ["i", "dna"]:
            continue

        # Update quote and bracket levels
        if token.text in ['"', "'"]:
            quote_level += 1
            if quote_level % 2 == 1:
                in_quotes = True
            else:
                in_quotes = False
        elif token.text in ["[", "("]:
            bracket_level += 1
            in_brackets = True
        elif token.text in ["]", ")"]:
            bracket_level -= 1
            if bracket_level == 0:
                in_brackets = False

        # Check if it's the first word in the document
        is_first_word_in_doc = token_start == first_word_index

        # Check if the token is at the beginning of a sentence
        is_first_word_in_sentence = any(sb == token_start for sb in sentence_boundaries)

        # Rule: If the word is capitalized and it's not the first word in a sentence, it's an error
        if (
            token.tag_ != "NNP"
            and token.text[0].isupper()
            and not in_quotes
            and not in_brackets
            and not is_first_word_in_sentence
            and not is_first_word
            and not is_first_word_in_doc
        ):
            if token.text in ["Latin", "X-ray", "X"]:
                continue
            num_errors += 1
            errors.append(
                f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence"
            )
            grammar_mistakes.append((token.text))
            grammatical_indices.append(
                (
                    token_start,
                    token_start + len(token.text),
                    f"Improper capitalization: '{token.text}' is capitalized but not a proper noun or start of a sentence",
                )
            )

        # Rule 1: Proper noun should not be lower case
        if (
            token.tag_ == "NNP"
            and token.text.islower()
            and token.text not in ["physics", "considereng", "learning"]
        ):
            if token.text == "café":
                continue
            num_errors += 1
            errors.append(f"Lowercase proper noun: '{token.text}'")
            grammar_mistakes.append((token.text))
            grammatical_indices.append(
                (
                    mistake_start_idx,
                    mistake_end_idx,
                    f"Lowercase proper noun: '{token.text}'",
                )
            )

        # Rule 2: Use of 'whom' instead of 'who' in subject position
        if token.text.lower() == "whom" and (
            token.dep_ == "nsubj" or token.dep_ == "nsubjpass"
        ):
            num_errors += 1
            errors.append("Use of 'whom' instead of 'who' in subject position")
            grammar_mistakes.append(("whom"))
            grammatical_indices.append(
                (
                    mistake_start_idx,
                    mistake_end_idx,
                    "Use of 'whom' instead of 'who' in subject position",
                )
            )

        # Rule 3: Incorrect use of apostrophes ('s vs. s')
        if token.text == "'s":
            previous_token = token.nbor(-1)

            if token.head.pos_ in ["NUM"] and token.head.text != "one":
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for numbers.")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append(
                    (
                        mistake_start_idx - len(previous_token.text),
                        mistake_end_idx,
                        "Incorrect use of apostrophe ('s) for numbers.",
                    )
                )

            # Check if the token is not attached to a noun
            elif token.head.pos_ not in ["NOUN", "PROPN", "PRON", "VERB", "NUM", "AUX"]:
                print("Error::", token.head.pos_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for non-nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append(
                    (
                        mistake_start_idx - len(previous_token.text),
                        mistake_end_idx,
                        "Incorrect use of apostrophe ('s) for non-nouns",
                    )
                )

            # Check if the token is attached to a plural noun
            # elif token.head.tag_ == 'NNS':
            #     num_errors += 1
            #     errors.append("Incorrect use of apostrophe ('s) for plural nouns")
            #     errors.append(token)
            #     grammar_mistakes.append((previous_token.text + token.text))
            #     grammatical_indices.append((mistake_start_idx - len(previous_token.text), mistake_end_idx))

            # Check if the token is attached to a proper noun
            elif token.head.tag_ == "NNP" and not token.dep_ in ["poss", "case"]:
                print("TOKEN DEP::", token.dep_)
                num_errors += 1
                errors.append("Incorrect use of apostrophe ('s) for proper nouns")
                errors.append(token)
                grammar_mistakes.append((previous_token.text + token.text))
                grammatical_indices.append(
                    (
                        mistake_start_idx - len(previous_token.text),
                        mistake_end_idx,
                        "Incorrect use of apostrophe ('s) for proper nouns",
                    )
                )

        # Rule 4: Check for conjunction errors
        if token.pos_ == "CCONJ":
            head = token.head
            allowed_head_pos = [
                "NOUN",
                "PRON",
                "ADJ",
                "ADV",
                "ADP",
                "DET",
                "CCONJ",
                "SCONJ",
                "INTJ",
                "SYM",
                "VERB",
                "AUX",
                "PROPN",
            ]
            # print("TEXT::", token.text)
            if head.pos_ not in allowed_head_pos:
                print("HEAD POS::", head.pos_)
                print("TEXT::", token.text)
                num_errors += 1
                errors.append("Conjunction error: Incorrect use of conjunction")
                grammar_mistakes.append((token.text))
                grammatical_indices.append(
                    (
                        mistake_start_idx,
                        mistake_end_idx,
                        "Conjunction error: Incorrect use of conjunction",
                    )
                )

        # Rule 5: Check for 'a' before words with vowel sounds
        if token.text.lower() == "a":
            next_token = token.nbor()
            if next_token.text.lower() in vowels_not_starting_with_vowels:
                num_errors += 1
                errors.append("Use of 'a' before a word with a vowel sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append(
                    (
                        next_token.idx,
                        next_token.idx + len(next_token.text),
                        "Use of 'a' before a word with a vowel sound",
                    )
                )

            elif (
                next_token.text[0].lower() in "aeiou"
                and next_token.text.lower() not in words_with_consonant_sound
            ):
                num_errors += 1
                errors.append("Use of 'a' before a word with a vowel sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append(
                    (
                        next_token.idx,
                        next_token.idx + len(next_token.text),
                        "Use of 'a' before a word with a vowel sound",
                    )
                )

        # Rule 6: Check for 'an' before words with consonant sounds
        if token.text.lower() == "an":
            next_token = token.nbor()
            if next_token.text.lower() in vowels_not_starting_with_vowels:
                pass
            elif (
                next_token.text.lower() in words_with_consonant_sound
                or next_token.text[0].lower() not in "aeiou"
            ):
                num_errors += 1
                errors.append("Use of 'an' before a word with a consonant sound")
                grammar_mistakes.append((next_token.text))
                grammatical_indices.append(
                    (
                        next_token.idx,
                        next_token.idx + len(next_token.text),
                        "Use of 'an' before a word with a consonant sound",
                    )
                )

        # Rule 7: Check for punctuation mistakes
        if token.pos_ == "PUNCT":
            if token.text not in [
                ".",
                ",",
                "!",
                "?",
                ":",
                ";",
                "“",
                "”",
                "‘",
                "’",
                "—",
                "–",
                "-",
                '"',
                "'",
                "(",
                ")",
                "[",
                "]",
                "{",
                "}",
                "/",
                "\\",
                "_",
                "*",
                "&",
                "@",
                "#",
                "$",
                "%",
                "^",
                "<",
                ">",
                "|",
                "`",
                "~",
                "+",
                "=",
                "..",
                "...",
                "¿",
                "¡",
            ]:
                num_errors += 1
                errors.append(f"Unexpected punctuation: '{token.text}'")
                grammar_mistakes.append((token.text))
                grammatical_indices.append(
                    (
                        mistake_start_idx,
                        mistake_end_idx,
                        f"Unexpected punctuation: '{token.text}'",
                    )
                )

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

    print("Number of duplicates removed:", num_duplicates)
    print("Unique grammatical indices:", unique_grammatical_indices)

    num_errors = len(unique_grammatical_indices)
    print("Number of grammatical errors:", num_errors)

    if num_errors > 0:
        print("Grammatical errors detected:")
        for error in errors:
            print("-", error)

    if num_errors == 0:
        pass
    elif num_errors == 1:
        score -= 0.5
    elif num_errors == 2:
        score -= 1.0
    elif num_errors == 3:
        score -= 1.5
    else:
        score = 0.0

    grammatical_indices = unique_grammatical_indices
    # print("Grammatical Mistakes", grammar_mistakes)

    return score, grammar_mistakes, grammatical_indices


def calculate_vocab_range_score_email(email_text, form_score, grammar_score):

    vocab_score = 2.0
    if grammar_score == 0.0:
        print("BECAUSE GRAMMAR SCORE IS 0, I AM HERE.")
        vocab_score -= 1.0
    # Tokenize the email into words (you might need to preprocess the text further)
    words = email_text.lower().split()

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
            vocab_score = (
                (total_unique_words - low_threshold)
                / (high_threshold - low_threshold)
                * 2
            )
            score = min(
                round(vocab_score, 2), form_score
            )  # Ensure vocab score doesn't exceed form score
            print("HELLO 2")
        return score


def calculate_spelling_score(summary, accent, grammatical_indices):
    if accent == "en-us":
        dictionary = enchant.Dict("en_US")
    elif accent == "en-uk":
        dictionary = enchant.Dict("en_GB")

    words = re.finditer(r"\b\w+\b", summary)  # Using re.finditer to get word indices
    word_list = list(words)  # Convert the iterator to a list to work with

    # Remove the last word from consideration
    if word_list:
        word_list = word_list[:-1]

    print("Word List:::", word_list)
    misspelled_corrected = {}
    misspelled_words = 0
    misspelled_word_indices = []  # Initialize list for misspelled word indices

    # Check for all occurrences of the phrase "mind set"
    mind_set_matches = re.finditer(r"\bmind set\b", summary)
    for match in mind_set_matches:
        start_index = match.start()
        end_index = match.end()
        misspelled_corrected["mind set"] = "mindset"
        misspelled_words += 1
        misspelled_word_indices.append((start_index, end_index))

    for match in word_list:
        start_index = match.start()
        end_index = match.end()
        word = summary[start_index:end_index]
        if not dictionary.check(word):
            suggestions = dictionary.suggest(word)
            if suggestions:
                corrected_word = suggestions[
                    0
                ]  # Choosing the first suggestion as the corrected word
                if len(word) > 2 and word.replace(" ", "") == corrected_word.replace(
                    " ", ""
                ):
                    # If the original word and suggested word without spaces are the same,
                    # it's likely a compound word that was split incorrectly
                    continue
                # Check if the starting or ending index of the misspelled word matches with any grammatical index
                if any(
                    start_index == g_start or end_index == g_end
                    for g_start, g_end, g_end1 in grammatical_indices
                ):
                    continue  # Skip counting the misspelled word and excluding it from the corrected words
                if word.lower() in WORD_LIST:
                    continue  # Skip the word "multitaskers"
                misspelled_corrected[word] = corrected_word
                misspelled_words += 1
                misspelled_word_indices.append(
                    (start_index, end_index)
                )  # Store misspelled word indices

    print("Number of misspelled words:", misspelled_words)

    if misspelled_words == 0:
        score = 2.0
    elif misspelled_words == 1:
        score = 1.0
    else:
        score = 0.0

    return score, misspelled_corrected, misspelled_word_indices


def contains_only_bullet_points(text):
    """
    return true if any line starts with bullets points else false
    """
    bullet_points = ("*", "-", "•", "‣", "◦", "⁃")

    lines = text.split("\n")
    for line in lines:
        # Check if the line is not empty and doesn't start with a bullet point
        if line.strip() and line.strip().startswith(bullet_points):
            return True
    return False


def calculate_form_score_email(email):
    """
    If No issues in mail form, it checks following conditions. (Form mean - small case exist, - punc exists and - no sentence start with bullet points)
    - If word_count>= 50 and word_count<= 120 -> Max score
    - else If (word_count>= 30 and word_count<= 49) or (word_count>= 121 and word_count<= 140) -> Decrease by 1
    - else 0
    """

    # max form score
    form_score = 2.0

    # if punctuation exist -> true else false
    punc_check = any(char in string.punctuation for char in email)

    # if any sentence start with bullet point -> true else flase
    bullet_check = contains_only_bullet_points(email)

    # for all upper -> true else false
    check_case = email.isupper()

    word_count = len(email.split())
    print(f"\nWord count in email form score `{word_count}")

    if check_case == False and punc_check == True and bullet_check == False:
        print("No issues in email form.")

        if word_count >= 50 and word_count <= 120:
            print(f"email is between 50-120 words. Word count \n`{word_count}`")
            return form_score

        elif (word_count >= 30 and word_count <= 49) or (word_count >= 121 and word_count <= 140):
            print("email is between 30-49 or 121-140 words.\n")
            form_score -= 1.0
            return form_score

        else:
            print(f"Email form satisfies no word count conditions. Form score set to 0.\n")
            return 0.0
    else:
        print("Email form condition not satisfied. Form score set to 0.\n")
        return 0.0


def calculate_organization_score(email):
    starting_words = ["Dear", "Hello", "Good", "Greetings", "To", "Hi", "Hey"]
    ending_phrases = [
        "Yours sincerely,",
        "Yours faithfully,",
        "Regards,",
        "Best regards,",
        "Thanks,",
        "Thanks and Regards,",
        "Thanks & Regards,",
        "Thank you for your time,",
        "Looking forward to hearing from you,",
        "Sincerely,",
        "Faithfully,",
        "Best,",
        "All the best,",
        "Take care,",
        "Have a great day,",
        "Have a great week,",
        "Have a great weekend,",
        "Have a great month,",
        "Have a great year,",
        "Kind Regards,",
        "Kind regards,",
        "Warm Regards,",
        "Warm regards," "yours sincerely,",
        "Yours Sincerely,",
        "yours faithfully,",
        "Yours Faithfully,",
        "Regards,",
        "regards,",
        "best regards,",
        "Best Regards,",
        "thanks,",
        "thanks and regards,",
        "thanks & regards,",
        "Thanks and regards,",
        "thanks and regards,",
        "thank you for your time,",
        "looking forward to hearing from you,",
        "sincerely,",
        "faithfully,",
        "best,",
        "all the best,",
        "take care,",
        "have a great day,",
        "have a great week,",
        "have a great weekend,",
        "have a great month,",
        "have a great year,",
        "kind regards,",
        "Kind regards,",
        "warm regards,",
        "Warm regards,",
        "Best Wishes",
        "best wishes,",
        "Best wishes,",
        "Love,",
        "love," "Your friend,",
        "Your Friend,",
        "your friend,",
        "Your bestfriend,",
        "your bestfriend,",
        "Your Bestfriend,",
        "Cheers,",
        "cheers,",
        "Yours Lovingly,",
        "yours lovingly,",
        "With Regards,",
        "with regards,",
        "With regards,",
        "With Regard,",
        "with regard,",
        "With regard,",
        "Lots of Love,",
        "Lots of love,",
        "lots of love,",
        "Thanking You,",
        "Thanking you,",
        "thanking you,",
        "kind regard,",
        "Kind regard,",
        "Kind Regard,",
        "Thank You,",
        "Thank you,",
        "Your Best Friend,",
        "Your best friend,",
        "Your father,",
        "Your Father,",
        "Your Son,",
        "Your son,",
        "Your Daughter,",
        "Your daughter,",
        "Your Mother,",
        "Your mother,",
        "Yours sincerely",
        "Yours faithfully",
        "Regards",
        "Best regards",
        "Thanks",
        "Thanks and Regards",
        "Thanks & Regards",
        "Thank you for your time",
        "Looking forward to hearing from you",
        "Sincerely",
        "Faithfully",
        "Best",
        "All the best",
        "Take care",
        "Have a great day",
        "Have a great week",
        "Have a great weekend",
        "Have a great month",
        "Have a great year",
        "Kind Regards",
        "Kind regards",
        "Warm Regards",
        "Warm regards",
        "yours sincerely",
        "Yours Sincerely",
        "yours faithfully",
        "Yours Faithfully",
        "Regards",
        "regards",
        "best regards",
        "Best Regards",
        "thanks",
        "thanks and regards",
        "thanks & regards",
        "Thanks and regards",
        "thanks and regards",
        "thank you for your time",
        "looking forward to hearing from you",
        "sincerely",
        "faithfully",
        "best",
        "all the best",
        "take care",
        "have a great day",
        "have a great week",
        "have a great weekend",
        "have a great month",
        "have a great year",
        "kind regards",
        "Kind regards",
        "warm regards",
        "Warm regards",
        "Best Wishes",
        "best wishes",
        "Best wishes",
        "Love",
        "love",
        "Your friend",
        "Your Friend",
        "your friend",
        "Your bestfriend",
        "your bestfriend",
        "Your Bestfriend",
        "Cheers",
        "cheers",
        "Yours Lovingly",
        "yours lovingly",
        "With Regards",
        "with regards",
        "With regards",
        "With Regard",
        "with regard",
        "With regard",
        "Lots of Love",
        "Lots of love",
        "lots of love",
        "Thanking You",
        "Thanking you",
        "thanking you",
        "kind regard",
        "Kind regard",
        "Kind Regard",
        "Thank You",
        "Thank you",
        "Your Best Friend",
        "Your best friend",
        "Your father",
        "Your Father",
        "Your Son",
        "Your son",
        "Your Daughter",
        "Your daughter",
        "Your Mother",
        "Your mother",
    ]

    # Normalize newlines to handle various formats
    email = email.replace("\r\n", "\n").replace("\r", "\n")
    # Split into paragraphs based on newline
    paragraphs = email.split("\n")

    # Strip whitespace and remove empty paragraphs
    cleaned_list = [s.strip() for s in paragraphs if s.strip()]

    # Initial score
    score = 2.0  # Default to max score if there are at least 3 paragraphs

    # Check the number of paragraphs
    num_paragraphs = len(cleaned_list)
    print("Number of paragraphs:", num_paragraphs)

    if num_paragraphs == 0:
        # If no paragraphs are found, return 0.0
        return 0.0
    elif num_paragraphs < 3:
        # If fewer than 3 paragraphs, score is 0
        score = 0.0
    else:
        # Deduct points if starting paragraph is missing, empty, or doesn't start with a valid word
        if cleaned_list[0] == "" or not any(
            cleaned_list[0].startswith(word) for word in starting_words
        ):
            print("Cutting Due to this.")
            score -= 0.5

        print("CHECKER::::", cleaned_list[-3])
        # Deduct points if ending paragraph is missing, empty, or doesn't contain a valid phrase
        if cleaned_list[-2] == "" or not any(
            phrase in cleaned_list[-2] for phrase in ending_phrases
        ):
            print("Cutting Due to this 2.")
            score -= 0.5

        # Check if there's at least one paragraph that is neither the starting nor the ending paragraph
        # This validates that there's a body section in the email
        if len(cleaned_list) < 3:
            # Less than three paragraphs means no body
            return 0.0

    return score


def email_convention_score_func(email, question):

    capitalized_words = extract_capital_words(question)

    print("CAPITALIZED WORDS::::::", capitalized_words)
    # Normalize newlines to handle various formats
    email = email.replace("\r\n", "\n").replace("\r", "\n")
    # Split into paragraphs based on newline
    paragraphs = email.split("\n")

    print("PARAGRAPHS::::", paragraphs)
    # Strip whitespace and remove empty paragraphs
    cleaned_list = [s.strip() for s in paragraphs if s.strip()]

    # Initial score
    score = 2.0  # Default to max score if there are at least 3 paragraphs

    # Check the number of paragraphs
    num_paragraphs = len(cleaned_list)
    print("Number of paragraphs:", num_paragraphs)

    starting_words = ["Dear", "Hello", "Good", "Greetings", "To", "Hi", "Hey"]

    ending_phrases = [
        "Yours sincerely,",
        "Yours faithfully,",
        "Regards,",
        "Best regards,",
        "Thanks,",
        "Thanks and Regards,",
        "Thanks & Regards,",
        "Thank you for your time,",
        "Looking forward to hearing from you,",
        "Sincerely,",
        "Faithfully,",
        "Best,",
        "All the best,",
        "Take care,",
        "Have a great day,",
        "Have a great week,",
        "Have a great weekend,",
        "Have a great month,",
        "Have a great year,",
        "Kind Regards,",
        "Kind regards,",
        "Warm Regards,",
        "Warm regards," "yours sincerely,",
        "Yours Sincerely,",
        "yours faithfully,",
        "Yours Faithfully,",
        "Regards,",
        "regards,",
        "best regards,",
        "Best Regards,",
        "thanks,",
        "thanks and regards,",
        "thanks & regards,",
        "Thanks and regards,",
        "thanks and regards,",
        "thank you for your time,",
        "looking forward to hearing from you,",
        "sincerely,",
        "faithfully,",
        "best,",
        "all the best,",
        "take care,",
        "have a great day,",
        "have a great week,",
        "have a great weekend,",
        "have a great month,",
        "have a great year,",
        "kind regards,",
        "Kind regards,",
        "warm regards,",
        "Warm regards,",
        "Best Wishes",
        "best wishes,",
        "Best wishes,",
        "Love,",
        "love," "Your friend,",
        "Your Friend,",
        "your friend,",
        "Your bestfriend,",
        "your bestfriend,",
        "Your Bestfriend,",
        "Cheers,",
        "cheers,",
        "Yours Lovingly,",
        "yours lovingly,",
        "With Regards,",
        "with regards,",
        "With regards,",
        "With Regard,",
        "with regard,",
        "With regard,",
        "Lots of Love,",
        "Lots of love,",
        "lots of love,",
        "Thanking You,",
        "Thanking you,",
        "thanking you,",
        "kind regard,",
        "Kind regard,",
        "Kind Regard,",
        "Thank You,",
        "Thank you,",
        "Your Best Friend,",
        "Your best friend,",
        "Your father,",
        "Your Father,",
        "Your Son,",
        "Your son,",
        "Your Daughter,",
        "Your daughter,",
        "Your Mother,",
        "Your mother,",
        "Yours sincerely",
        "Yours faithfully",
        "Regards",
        "Best regards",
        "Thanks",
        "Thanks and Regards",
        "Thanks & Regards",
        "Thank you for your time",
        "Looking forward to hearing from you",
        "Sincerely",
        "Faithfully",
        "Best",
        "All the best",
        "Take care",
        "Have a great day",
        "Have a great week",
        "Have a great weekend",
        "Have a great month",
        "Have a great year",
        "Kind Regards",
        "Kind regards",
        "Warm Regards",
        "Warm regards",
        "yours sincerely",
        "Yours Sincerely",
        "yours faithfully",
        "Yours Faithfully",
        "Regards",
        "regards",
        "best regards",
        "Best Regards",
        "thanks",
        "thanks and regards",
        "thanks & regards",
        "Thanks and regards",
        "thanks and regards",
        "thank you for your time",
        "looking forward to hearing from you",
        "sincerely",
        "faithfully",
        "best",
        "all the best",
        "take care",
        "have a great day",
        "have a great week",
        "have a great weekend",
        "have a great month",
        "have a great year",
        "kind regards",
        "Kind regards",
        "warm regards",
        "Warm regards",
        "Best Wishes",
        "best wishes",
        "Best wishes",
        "Love",
        "love",
        "Your friend",
        "Your Friend",
        "your friend",
        "Your bestfriend",
        "your bestfriend",
        "Your Bestfriend",
        "Cheers",
        "cheers",
        "Yours Lovingly",
        "yours lovingly",
        "With Regards",
        "with regards",
        "With regards",
        "With Regard",
        "with regard",
        "With regard",
        "Lots of Love",
        "Lots of love",
        "lots of love",
        "Thanking You",
        "Thanking you",
        "thanking you",
        "kind regard",
        "Kind regard",
        "Kind Regard",
        "Thank You",
        "Thank you",
        "Your Best Friend",
        "Your best friend",
        "Your father",
        "Your Father",
        "Your Son",
        "Your son",
        "Your Daughter",
        "Your daughter",
        "Your Mother",
        "Your mother",
    ]

    email_lines = email.splitlines()

    # print("SECOND WORD FOUND:::::", email_lines[0].strip().split(1))
    first_line_words = [word.rstrip(".,?!") for word in email_lines[0].strip().split()]
    length = len(first_line_words)
    if first_line_words[length - 1] != "":
        print("FIRST LINE WORDS::", first_line_words[length - 1])

    if num_paragraphs >= 3:
        # print("Ending Line::" , email_lines[-3].strip())
        if email_lines[0].strip().split()[0] in starting_words and (
            first_line_words[length - 1] in capitalized_words
            or first_line_words[length - 2] in capitalized_words
        ):
            score -= 0
        else:
            print("I AM HERE BOSS")
            score -= 1

        print("Ending Line::", email_lines[-3].strip())
        if (
            email_lines[-2].strip() in ending_phrases
            or email_lines[-3].strip() in ending_phrases
        ):
            score -= 0
        else:
            print("I AM HERE BOSS 2")
            score -= 1

    elif num_paragraphs == 2:
        if email_lines[0].strip().split()[0] in starting_words and (
            first_line_words[length - 1] in capitalized_words
            or first_line_words[length - 2] in capitalized_words
        ):
            score -= 0
        else:
            score -= 1

        if email_lines[-2].strip() in ending_phrases:
            score -= 0
        else:
            score -= 1

    elif num_paragraphs == 1:
        if email_lines[0].strip().split()[0] in starting_words and (
            first_line_words[length - 1] in capitalized_words
            or first_line_words[length - 2] in capitalized_words
        ):
            score -= 0
        else:
            score -= 1

        if email_lines[0].strip() in ending_phrases:
            score -= 0
        else:
            score -= 1

    elif num_paragraphs == 0:
        score = 0.0

    if score < 0:
        score = 0

    return score


def score_email(email, question, major_aspect, minor_aspect, accent):
    # no main purpose of scores dict
    scores = {}

    content_score = calculate_content_score(email, question, major_aspect, minor_aspect)
    scores["content_score"] = content_score

    grammar_score, grammar_mistakes, grammatical_indices = (
        calculate_grammar_score_email(email)
    )

    spelling_score, correct_words, misspelled_indices = calculate_spelling_score(
        email, accent, grammatical_indices
    )

    form_score = calculate_form_score_email(email)
    scores["form_score"] = form_score

    vocab_range_score = calculate_vocab_range_score_email(
        email, form_score, grammar_score
    )

    organization_score = calculate_organization_score(email)

    email_convention_score = email_convention_score_func(email, question)

    if form_score == 0 or content_score == 0:
        content_score = 0
        grammar_score = 0
        vocab_range_score = 0
        spelling_score = 0
        correct_words = 0
        form_score = 0
        organization_score = 0
        email_convention_score = 0
    comments = set_email_comments(
        content_score,
        grammar_score,
        vocab_range_score,
        spelling_score,
        form_score,
        organization_score,
        email_convention_score,
    )

    total_score = (
        content_score
        + grammar_score
        + vocab_range_score
        + spelling_score
        + form_score
        + organization_score
        + email_convention_score
    )
    total_score = round(total_score, 1)
    updated_score = round(total_score * 4) / 4

    return (
        content_score,
        grammar_score,
        vocab_range_score,
        spelling_score,
        form_score,
        organization_score,
        updated_score,
        correct_words,
        comments,
        grammar_mistakes,
        misspelled_indices,
        grammatical_indices,
        email_convention_score,
    )

    raise Exception("Intentional exception!! + Score: ", scores)
