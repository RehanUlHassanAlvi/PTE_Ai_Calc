import re
import requests

def fetch_word_lists():
    url = "https://raw.githubusercontent.com/hyperreality/American-British-English-Translator/master/data/"
    uk_to_us = requests.get(url + "british_spellings.json").json()
    us_to_uk = requests.get(url + "american_spellings.json").json()
    us_only = requests.get(url + "american_only.json").json()
    uk_only = requests.get(url + "british_only.json").json()

    uk_words = set(uk_to_us) | set(uk_only)
    us_words = set(us_to_uk) | set(us_only)
    return uk_words, us_words

def get_dialect(text):
    uk_words, us_words = fetch_word_lists()
    uk_phrases = {w for w in uk_words if len(w.split()) > 1}
    us_phrases = {w for w in us_words if len(w.split()) > 1}
    uk_words -= uk_phrases
    us_words -= us_phrases
    max_length = max(len(word.split()) for word in uk_phrases | us_phrases)

    words = re.findall(r"([a-z]+)", text.lower()) # list of lowercase words only
    uk = 0
    us = 0
    # Check for multi-word phrases first, removing them if they are found
    for length in range(max_length, 1, -1):
        i = 0
        while i + length <= len(words):
            phrase = " ".join(words[i:i+length])
            if phrase in uk_phrases:
                uk += length
                words = words[:i] + words[i + length:]
            elif phrase in us_phrases:
                us += length
                words = words[:i] + words[i + length:]
            else:
                i += 1

    # Add single words
    uk += sum(word in uk_words for word in words)
    us += sum(word in us_words for word in words)

    if uk > us:
        return "en-uk"
    if us > uk:
        return "en-us"
    return "Unknown"


def check_accent(essay):
    if re.search(r'[.!?]', essay):
      sentences = re.split(r'[.!?]', essay)

      sentences=sentences[:-1]
      benchmark_accent = 'en-us'
      for i, sentence in enumerate(sentences):

          if get_dialect(sentence) != 'Unknown':
              benchmark_accent = get_dialect(sentence)

              return sentences,benchmark_accent,i
          elif i== len(sentences)-1:
             benchmark_accent="en-us"
             return sentences,benchmark_accent,i
    else:
        print("No punctuation found")
        accent=get_dialect(essay)
        if accent=='Unknown':
            accent='en-us'
        sen='1'
        return sen,accent,0
        

def identify_accent(essay):
    us_english = ["aluminum", "analyze", "behavior", "center", "check", "color", "catalog", "defense", "dialog", "favorite",
                  "fiber", "glamor", "gray", "honor", "jewelry", "liter", "meter", "mold", "neighbor", "organize",
                  "pediatric", "plow", "pajamas", "realize", "theater", "traveling", "skeptic", "sulfur", "ton",
                  "tire", "whiskey", "yogurt", "mustache", "gage", "donut", "counseling", "disk", "maneuver",
                  "revealed", "program", "license", "enroll", "aeroplane", "check", "gluing", "honed", "curb",
                  "pretense", "saltpeter", "apologize", "artificialize", "authorize", "capitalize", "categorize",
                  "civilize", "emphasize", "equalize", "finalize", "globalize", "harmonize", "initialize",
                  "legalize", "memorize", "minimize", "organize", "prioritize", "realize", "recognize", "specialize",
                  "stabilize", "utilize", "analyze", "breathalyze", "defense", "offense", "license", "preferable",
                  "enroll", "fulfill", "mom", "tyre", "center", "meter", "liter", "dialog", "plow", "glamor", "gray",
                  "jewelry", "favor", "favored", "favoring", "emphasizes", "behavioral", "realized","canceled", "utilized","utilize", "summarized", "heard", "benefiting", "revolutionizes", "revolutionize", "revolutionizing", "revolutionized"]

    uk_english = ["aluminium", "analyse", "behaviour", "centre", "cheque", "colour", "catalogue", "defence", "dialogue",
                  "favourite", "fibre", "glamour", "grey", "honour", "jewellery", "litre", "metre", "mould", "neighbour",
                  "organise", "paediatric", "plough", "pyjamas", "realise", "theatre", "travelling", "sceptic", "sulphur",
                  "tonne", "tyre", "whisky", "yoghurt", "moustache", "gauge", "doughnut", "counselling", "disc", "manoeuvre",
                  "revealed", "programme", "licence", "enrol", "aeroplane", "cheque", "glueing", "honed", "kerb", "pretence",
                  "saltpetre", "apologise", "artificialise", "authorise", "capitalise", "categorise", "civilise", "emphasise",
                  "equalise", "finalise", "globalise", "harmonise", "initialise", "legalise", "memorise", "minimise", "organise",
                  "prioritise", "realise", "recognise", "specialise", "stabilise", "utilise", "analyse", "breathalyse", "defence",
                  "offence", "licence", "preferable", "enrol", "fulfil", "mum", "tire", "centre", "metre", "litre", "dialogue",
                  "plough", "glamour", "grey", "jewellery", "favour", "favoured", "favouring", "emphasises", "behavioural", "realised","cancelled","utilised","utilise", "summarised", "heared", "benefitting", "revolutionises", "revolutionise", "revolutionising", "revolutionised"]

    # us_detected = []
    # uk_detected = []

    words = essay.split()
    for word in words:
        if word.lower() in us_english:
            return "en-us"
        elif word.lower() in uk_english:
            return "en-uk"
        
    print("- Default en-us")
    return "en-us"
    # if accent not detected return 
    # return "en-us"
    # print(us_detected)
    # print(uk_detected)
    # if len(us_detected) > len(uk_detected):
    #     return "en-us"
    # elif len(us_detected) < len(uk_detected):
    #     return "en-uk"
    # else:
    #     return "en-us"



def check_accent_summary(summary):

      accent=get_dialect(summary)
      return accent
            




def compare_accents(sentences,benchmark_accent,index):

    # sentences = re.split(r'[.!?]', essay)

    # benchmark_accent = 'en-us'
    # for i, sentence in enumerate(sentences):
    #     if get_dialect(sentence) != 'Unknown':
    #         benchmark_accent = get_dialect(sentence)

    #         break


    different_accent_count = 0

    index=index+1
    for sentence in sentences[index:]:
        if get_dialect(sentence) != benchmark_accent and get_dialect(sentence)!='Unknown':


            different_accent_count += 1
        index+=1

    return different_accent_count


def calculate_deductions(diff,grammar_score,spelling_score,coherence_score):
    print("Scores without Deduction")
    print("grammer: ",grammar_score)
    print("spelling: ",spelling_score)
    print("Development and coherence structure score: ",coherence_score)
    if diff > 15:
        grammar_score -= 0.75
        spelling_score -= 0.75
        coherence_score -= 0.75
    elif diff > 8:
        grammar_score -= 0.5
        spelling_score -= 0.5
        coherence_score -= 0.5
    elif diff > 3:
        grammar_score -= 0.25
        spelling_score -= 0.25
        coherence_score -= 0.25
    
    
    print("Scores after Deduction")
    print("grammer: ",grammar_score)
    print("spelling: ",spelling_score)
    print("Development and coherence structure score: ",coherence_score)
    return grammar_score,spelling_score,coherence_score

def calculate_deductions_mail(diff,grammar_score,spelling_score):
    print("Scores without Deduction")
    print("grammer: ",grammar_score)
    print("spelling: ",spelling_score)
    if diff > 15:
        grammar_score -= 0.75
        spelling_score -= 0.75

    elif diff > 8:
        grammar_score -= 0.5
        spelling_score -= 0.5

    elif diff > 3:
        grammar_score -= 0.25
        spelling_score -= 0.25

    
    
    print("Scores after Deduction")
    print("grammer: ",grammar_score)
    print("spelling: ",spelling_score)
    return grammar_score,spelling_score





def calculate_deductions_summary(diff,grammar_score):
    print("Scores without Deduction")
    print("grammer: ",grammar_score)

    if diff > 1:
        grammar_score -=0.5
    elif diff > 2: 
        grammar_score -=1.0


    
    
    print("Scores after Deduction")
    print("grammer: ",grammar_score)
    return grammar_score
