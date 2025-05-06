import nltk
from nltk.stem import PorterStemmer
import spacy
from collections import Counter
import string 

porter_stemmer = PorterStemmer()

nlp = spacy.load("en_core_web_sm")


def remove_punctuation_and_lower(text):
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    return cleaned_text



def generate_word_status_dict_for_major_and_minor_for_less_para(stemmed_major_aspect,stemmed_minor_aspect ,stemmed_email_words):
    word_status_dict = {}
    
    word_status_dict2 = {}

    for word in stemmed_major_aspect:
        status = 1 if word in stemmed_email_words else 0
        word_status_dict[word] = [status]

    for word in stemmed_minor_aspect:
        status = 1 if word in stemmed_email_words else 0
        word_status_dict2[word] = [status]

    return word_status_dict,word_status_dict2



def generate_word_status_for_major_dict(stemmed_major_aspect, main_body_major_aspect_counts):
    word_status_dict = {}

    for word in stemmed_major_aspect:
        count_status = 1 if main_body_major_aspect_counts.get(word, 0) >= 1 else 0
        word_status_dict[word] = [ count_status]

    return word_status_dict



def generate_multiword_status_for_major_dict(major_aspect, main_body):
    major_aspect=convert_to_lowercase(major_aspect)
    word_status_dict = {}

    for word in major_aspect:
        count_status = 1 if main_body.count(word) >= 1 else 0
        word_status_dict[word] = [count_status]

    return word_status_dict


def generate_multiword_status_for_minor_dict(minor_aspect, main_body):
    minor_aspect=convert_to_lowercase(minor_aspect)
    word_status_dict = {}

    for word in minor_aspect:
        count_status = 1 if main_body.count(word) >= 1 else 0
        word_status_dict[word] = [ count_status]
    print("WORD STATUS DICT::", word_status_dict)
    return word_status_dict


def generate_all_words_aspects_dict(major_aspect, minor_aspect,email_words):
    major_aspect=convert_to_lowercase(major_aspect)
    word_status_dict = {}
    word_status_dict1 = {}

    for word in major_aspect:
        status = 1 if word in email_words else 0
        word_status_dict[word] = []

    for word in minor_aspect:
        status = 1 if word in email_words else 0
        word_status_dict1[word] = [status]
     
    return word_status_dict,word_status_dict1


def generate_word_status_for_minor_dict(stemmed_minor_aspect, main_body_minor_aspect_counts):
    def process_word(word):

        count_status = 1 if main_body_minor_aspect_counts.get(word, 0) >= 1 else 0
        return [count_status]

    def process_nested_list(nested_list):
        if isinstance(nested_list, list):
            return [process_nested_list(sublist) for sublist in nested_list]
        else:
            return process_word(nested_list)

    return process_nested_list(stemmed_minor_aspect)


def major_scoring(major_aspects_status_dict, para_len, content_score):
    print("CONTENT NUMBER OF PARAGRAPHS:::", para_len)
    if para_len >= 3:
        total_score= content_score
        score= total_score

        # Skip starting and last 2 paragraphs
        body_status = [statuses for i, statuses in enumerate(major_aspects_status_dict.values()) if i not in [para_len]]

        print("Body Statuses:::", body_status)

        # Count the number of major aspects mentioned in the body
        major_count = sum(any(status == 1 for status in statuses) for statuses in body_status)


        # Deduct marks based on the number of major aspects mentioned
        if major_count >= 3:
            print("3 major aspects mentioned, no deduction")
        elif major_count == 2:
            print("2 major aspects mentioned, deduct 0.75 marks")
            score -= 0.75
        elif major_count == 1:
            print("1 major aspect mentioned, deduct 1.25 marks")
            score -= 1.25
        else:
            print("No major aspects mentioned, give 0 marks")
            score = 0.0

        if score <= 0.0:
            score = 0.0
        return score
    
    else:
        total_score= content_score - 1.0
        score=total_score
        return score
    
        
def check_minor_aspects(aspects_status_dict, minor_aspects):
    # Flatten the list of minor aspects
    flattened_minor_aspects = flatten_list(minor_aspects)
    
    # Check if any of the flattened minor aspects are mentioned
    for aspect in flattened_minor_aspects:
        if aspect in aspects_status_dict:
            return True
    return False


# Function to check if a list is multi-dimensional
def is_multi_dimensional(lst):
    return any(isinstance(elem, list) for elem in lst)


def minor_scoring(minor_aspects_status_dict, major_score, para_len):
    score = major_score

    # minor_aspects = [[1, 1, 1],[1, 1, 1], [[1, 1, 0], [0, 0, 1]]]
    nested_start_index = find_nested_start(minor_aspects_status_dict)
    print("Index of the start of nested array:", nested_start_index)

    print("MINOR ASPECTS:::", minor_aspects_status_dict)
    
    # If major_score is 0.0, return 0.0
    if score == 0.0:
        return score
    

    print("PARAGRAPH LENGTH:::", para_len)
    if para_len >= 3:
        if nested_start_index != -1:
            value = minor_aspects_status_dict[:nested_start_index] 
            value2= minor_aspects_status_dict[nested_start_index:] 
            print("Value::",value)
            print("Value2::",value2)


            adder = [sum(subsublist) for sublists in value2 for subsublist in zip(*sublists)]
            print("ADDER:::", adder)
            result = [1 if val > 1 else val for val in adder]
            print("RESULT:::", result)
            print(result)
            # print(result)
            if isinstance(value, list):
                value.append(result)
                print("Value after appending::",value)

                print("LENGTH OF VALUE:::", len(value))
                zero_count = sum(all(status == 0 for status in statuses) for statuses in value)
                mixed_count = sum(1 for statuses in value if any(status == 0 for status in statuses) and any(status == 1 for status in statuses))

                print("ZERO::", zero_count)
                    
                # If one minor is not mentioned in any section, cut 1 mark
                if zero_count > 0:
                    print("If one minor aspect is not mentioned.")
                    deduction = min(zero_count*0.25, 1)
                    score -= deduction
                else:
                    score-= 0

        # return score
            return score
        
        else:

            print("I AM IN ELSE.")
            print("MINOR ASPECT STATUS DICT IN ELSE:::", minor_aspects_status_dict)
            # if isinstance(minor_aspects_status_dict, dict):
            #     # Filter out keys with all zero values
            #     minor_aspects_status_dict = {key: value for key, value in minor_aspects_status_dict.items() if any(status != 0 for status in value)}
            # elif isinstance(minor_aspects_status_dict, list):
            #     minor_aspects_status_dict = [item for item in minor_aspects_status_dict if any(status != 0 for status in item)]


            print("MINOR ASPECTS STATUS DICT....:::", minor_aspects_status_dict)
            # If no items remain after filtering, return the major score as there are no minor aspects to score
            if not minor_aspects_status_dict:
                return major_score

            if isinstance(minor_aspects_status_dict, dict):
                zero_count = sum(all(status == 0 for status in statuses) for statuses in minor_aspects_status_dict.values())
                print("ZERO COUNT DICT:::::", zero_count)
            else:
                zero_count = sum(all(status == 0 for status in item) for item in minor_aspects_status_dict)
                print("ZERO COUNT LIST:::::", zero_count)
            print("ZERO COUNT:::::", zero_count)



            # If one minor is not mentioned in any section, cut 1 mark
            if zero_count > 0:
                print("If one minor aspect is not mentioned.")
                deduction = min(zero_count*0.25, 1)
                score -= deduction
            else:
                score-= 0

            if score <= 0.0:
                score = 0.0

            return score
        

    else:
        # Filter out keys with all zero values
        minor_aspects_status_dict = {key: value for key, value in minor_aspects_status_dict.items() if any(status != 0 for status in value)}

        # If no keys remain after filtering, return the major score as there are no minor aspects to score
        if not minor_aspects_status_dict:
            return major_score
        
        zero_count = sum(all(status == 0 for status in statuses) for statuses in minor_aspects_status_dict.values())

        # If one minor is not mentioned in any section, cut 1 mark
        if zero_count > 0:
            print("If one minor aspect is not mentioned.")
            deduction = min(zero_count*0.25, 1)
            score -= deduction
        else:
            score-= 0

        if score <= 0.0:
            score = 0.0

        return score
    

def find_nested_start(lst):
    for i, item in enumerate(lst):
        if isinstance(item, list):
            for subitem in item:
                if isinstance(subitem, list):
                    return i
    return -1


# Helper function to flatten nested lists
def flatten(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list




def scoring(major_aspects_status_dict,minor_aspects_status_dict,para_len,content_score):
  print("IN SCORING",content_score)
  major_score= major_scoring(major_aspects_status_dict,para_len,content_score)
  total_score= minor_scoring(minor_aspects_status_dict,major_score,para_len)

  return total_score




def detect_values_with_spaces(string_list):
    values_with_spaces = []
    for value in string_list:
        if ' ' in value:
            values_with_spaces.append(value)
    return values_with_spaces


def stem_words(word_list):
    return [porter_stemmer.stem(word) for word in word_list]



def flatten_list(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


def stem_words2(word_list):
    def simplestem_word(word):
        # Stem each word using a Porter stemmer
        return porter_stemmer.stem(word)

    def stem_nested_list(nested_list):
        # Recursively apply stemming to nested lists
        if isinstance(nested_list, list):
            return [stem_nested_list(sublist) for sublist in nested_list]
        else:
            return simplestem_word(nested_list)

    # Apply stemming while maintaining the structure
    return stem_nested_list(word_list)



def convert_to_lowercase(string_list):
    return [s.lower() for s in string_list] 


def dealing_multi_words_major_aspects_aspect( major_aspect_with_spaces,intro_words,conc_words,main_body_words):

    major_aspect_with_spaces=convert_to_lowercase(major_aspect_with_spaces)
    print("")
    # print("major_aspect_with_spaces: ",major_aspect_with_spaces)

    intro_major_multiword_aspect_count = sum(1 for word in major_aspect_with_spaces  if word in intro_words )
    print("")
    # print("intro_major_multiword_aspect_count: ",intro_major_multiword_aspect_count)

    conc_major_multiword_aspect_count = sum(1 for word in  major_aspect_with_spaces if word in conc_words)
    # print("conc_major_multiword_aspect_count: ",conc_major_multiword_aspect_count)

    
    main_body_major_multiword_aspect_counts = sum(1 for word in major_aspect_with_spaces  if  main_body_words.count(word)>=2 )

    # print("main_body_major_multiword_aspect_presence: ",main_body_major_multiword_aspect_counts )

    return intro_major_multiword_aspect_count, conc_major_multiword_aspect_count, main_body_major_multiword_aspect_counts 





def dealing_multi_words_minor_aspects_aspect( minor_aspect_with_spaces,intro_words,conc_words,main_body_words):

    minor_aspect_with_spaces=convert_to_lowercase(minor_aspect_with_spaces)

    intro_minor_multiword_aspect_count = sum(1 for word in minor_aspect_with_spaces  if word in intro_words )
    print("")
    # print("intro_minor_multiword_aspect_count: ",intro_minor_multiword_aspect_count)

    conc_minor_multiword_aspect_count = sum(1 for word in  minor_aspect_with_spaces if word in conc_words)
    # print("conc_minor_multiword_aspect_count: ",conc_minor_multiword_aspect_count)

    
    main_body_minor_multiword_aspect_counts = sum(1 for word in minor_aspect_with_spaces  if  main_body_words.count(word)>=1 )


    # print("main_body_minor_multiword_aspect_presence: ", main_body_minor_multiword_aspect_counts )

    return intro_minor_multiword_aspect_count, conc_minor_multiword_aspect_count,  main_body_minor_multiword_aspect_counts 





def dealing_multi_words_major_aspects_aspect_less_para(major_aspect_with_spaces,email):
    major_aspect_with_spaces=convert_to_lowercase(major_aspect_with_spaces)
    print("")
    # print("major_aspect_with_spaces: ",major_aspect_with_spaces)
    count = sum(1 for word in major_aspect_with_spaces  if  email.count(word)>=2 )

    # print("email_major_multiword_aspect_presence_less_para: ",count )

    return count






def dealing_multi_words_minor_aspects_aspect_less_para(minor_aspect_with_spaces,email):
    minor_aspect_with_spaces=convert_to_lowercase(minor_aspect_with_spaces)
    print("")
    # print("minor_aspect_with_spaces: ",minor_aspect_with_spaces)
    count = sum(1 for word in  minor_aspect_with_spaces if word in email)

    # print("email_minor_multiword_aspect_presence_less_para: ",count )

    return count
