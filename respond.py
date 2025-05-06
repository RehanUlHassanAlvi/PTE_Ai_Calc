
from collections import Counter, defaultdict
from io import StringIO
import io
from pathlib import Path
import re
import string
import sys
import nltk
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os


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
    # Split the text into sentences
    sentences = nltk.sent_tokenize(text.lower())
    
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
    
    # print("N GRAM::", n_grams)
    # Count the occurrences of each n-gram
    n_gram_counts = Counter(all_n_grams)
    
    # Return the phrases that appear more than once and have at least 'n' words
    return {k: v for k, v in n_gram_counts.items() if v > 1 and len(k.split()) >= n}


def check_repeated_phrases(user_text):

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
    skip_phrases1 = phrases_to_check + ["also heard that", "also heard from", "also hear from","i also heard", "i also hear", "I also heard", "I also hear", "also talked about", "also explained about", "i also explained", "I also explained", "also explain about", "also explain that", "also explained that", "also explained about"]

    num_occurrences = 0

    for phrase in phrases_to_check:
        matches = re.finditer(r'\b' + re.escape(phrase) + r'\b', user_text)
        for match in matches:
            num_occurrences += 1

    return num_occurrences, skip_phrases1


def appropriacy_score(user_text, major_aspect, minor_aspect):
    apropricay_score = 3.0

    user_text = remove_punctuation_and_lower(user_text)

    
    # Split the user text into words/phrases for comparison
    user_text_words = set(user_text.lower().split())

    print("User words::", user_text_words)
    # Count the number of major aspects mentioned in the user text
    major_count = sum(1 for aspect in major_aspect if aspect.lower() in user_text_words)
    # Count the number of minor aspects mentioned in the user text
    minor_count = sum(1 for aspect in minor_aspect if aspect.lower() in user_text_words)

    print("Length of Major Aspect::", len(major_aspect))

    repetition_count, skip_phrases1 = check_repeated_phrases(user_text)

    print("Repitition Count::", repetition_count)

    recurring_phrases = find_recurring_phrases(user_text, n=3, skip_phrases=skip_phrases1)

    print("Recurring Phrases::", recurring_phrases)

    recurring_phrases1 = merge_phrases(recurring_phrases)

    print("Merged Recurring Phrases::", recurring_phrases1)

    count1 = len(recurring_phrases1)

    print("Count1::", count1)

    num_occurrences=0
    num_occurrences += count1

    print("Number of Occurences::", repetition_count)

    print("apropricay_score::", major_aspect)

    apropricay_score = (major_count / len(major_aspect)) * 60 + (minor_count / len(minor_aspect)) * 30



    if apropricay_score > 0:
        occur_scale  =  max(0, 1 - 0.30 * max(num_occurrences - 1, 0))
        phrase_scale =  max(0, 1 - 0.15 * max(repetition_count - 1, 0))
        unique_word_scale = min(len(user_text_words) / 50, 1.0)

        apropricay_score = apropricay_score * phrase_scale * occur_scale  * unique_word_scale

    comments= []
    # # Determine the content score based on the criteria
    if apropricay_score >= 80:
        comments.append("Great appropriacy score!")
    elif apropricay_score < 80:
        comments.append("Try to give more correct description to achieve better appropriacy marks.")



    print("No of Major Aspect Present::", major_count)
    print("No of Minor Aspect Present::", minor_count)

    print("Major Aspects:", major_aspect)
    print("User Text:", user_text)
    print("Minor Aspects:", minor_aspect)
    print("Apropriacy Score:", apropricay_score)

    return apropricay_score, comments


def calculate_fluency_score(apropricay_score, number_of_pauses, number_of_words, duration, conchecker, speaking_duration):
    print("Content Percentage::", apropricay_score)
    print("Number of Pauses::", number_of_pauses)
    print("Number of Words::", number_of_words)
    print("duration::", duration)
    comments = []
    CONTENT_WEIGHT = 30
    PAUSE_WEIGHT = 30
    WPS_WEIGHT = 30

    PAUSE_COST = 5
    LONG_PAUSE_COST = 10

    words = int(number_of_words)
    dur = float(duration)
    wps = (words - 1) / dur
    wps = round(wps, 2)
    print("Words Per Second::", wps)
    fluency_score = 5.0

    pauses = int(number_of_pauses)
    print(type(pauses))

    duration = float(duration)
    speaking_dur = float(speaking_duration)

    diffduration = duration - speaking_dur

    diffduration = round(diffduration,2)

    print("Difference Duration::", diffduration)
    #CORRECTION------------------------
    if pauses == 0:
        long_pause = 0
    else:
        long_pause = diffduration / pauses

    print("Long Pause::", long_pause)

    real_content_score = round((apropricay_score / 90) * CONTENT_WEIGHT)
    penalty = (pauses * PAUSE_COST) #+ (long_pause * LONG_PAUSE_COST)
    penalty_score = PAUSE_WEIGHT - penalty

    if 2.0 <= wps < 2.5:
        wps_score= WPS_WEIGHT
    elif 1.75 <= wps < 2.75:
        wps_score= WPS_WEIGHT - 10
    elif 1.65 <= wps < 2.85:
        wps_score= WPS_WEIGHT - 20
    else:
        wps_score= 0

    fluency_score=real_content_score+penalty_score+wps_score

    comments=[]

    if fluency_score >80:
        comments.append('Amazing Fluency')
    elif (fluency_score <80 & fluency_score>70):
        comments.append('Great Fluency')
    elif (fluency_score <70 & fluency_score>60):
        comments.append('Good Fluency')
    elif (fluency_score <60):
        comments.append('Fluency needs to be improved')


    return fluency_score, comments



def splitter(file):
    # Ensure the output directory exists
    output_dir = "splitter"
    os.makedirs(output_dir, exist_ok=True)

    # Load the audio file
    sound_file = AudioSegment.from_wav(file)

    # Get the duration of the audio file
    audio_duration = sound_file.duration_seconds

    # Split the audio into 2-second segments
    for i, start_time in enumerate(range(0, int(audio_duration), 3)):
        end_time = min(start_time + 3, audio_duration)
        segment = sound_file[int(start_time * 1000):int(end_time * 1000)]

        # Export the segment with two-digit formatting
        out_file = os.path.join(output_dir, f"{str(i+1).zfill(2)}.wav")
        print("Exporting", out_file)
        segment.export(out_file, format="wav")



def calculate_pronunciation_score():
    
    mysp = __import__("my-voice-analysis")

    pron_scores = {}

    # Define the temporary directory where the split audio files are stored
    temp_dir = "splitter"

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio files
    audio_dir = os.path.join(script_dir, temp_dir)
    
    print("AUDIO DIRECTORY::", audio_dir)

    # Iterate over all files in the specified directory
    for file_path in Path(audio_dir).glob("*.wav"):
        file_name = file_path.stem

        print("FILE NAME::", file_name)

        temp_path = os.path.join(audio_dir, file_name + '.wav')

        print("TEMP PATH::", temp_path)

        # Capture the output of mysp.mysptotal()
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            print("Filename::", file_name)
            print("Audio Directory::", audio_dir)
            mysp.mysppron(file_name, audio_dir)
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")

        sys.stdout = sys.__stdout__  # Reset redirect

        # Process the captured output to extract the data
        output = captured_output.getvalue()
        print("OUTPUT::", output)
        output_lines = output.strip().split('\n')

        # Extract pronunciation score from output
        pron_score = 0.0
        for line in output_lines:
            if "Pronunciation_posteriori_probability_score_percentage" in line:
                pron_score = float(line.split(':')[-1].strip())
                break

        # Classify the score
        classification = ""
        if pron_score >= 80:
            classification = "good"
        elif pron_score >= 60:
            classification = "average"
        else:
            classification = "bad"

        pron_scores[file_name] = {
            "score": pron_score,
            "classification": classification
        }


    # Calculate the average pronunciation score
    if pron_scores:
        avg_score = np.mean([score_info["score"] for score_info in pron_scores.values()])
    else:
        avg_score = 0.0

    score=(avg_score / 100)*90

    print("SCORE:::", score)

    # if 90 <= avg_score:
    #     score = 5.0
    # elif 70 <= avg_score < 90:
    #     score = 4.0
    # elif 55 <= avg_score < 70:
    #     score = 3.0
    # elif 30 <= avg_score < 55:
    #     score = 2.0
    # elif 5 <= avg_score < 30:
    #     score = 1.0
    # else:
    #     score = 0.0

    return pron_scores, score


def check_conclusion_phrases(text, conclusion_phrases):
    for phrase in conclusion_phrases:
        if phrase in text:
            return True
    return False

def remove_punctuation_and_lower(text):
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    return cleaned_text


def respondscoring(user_text, major_aspects, minor_aspects, pauses, duration, speaking_duration, file):
    apropriacy_score1, comments = appropriacy_score(user_text, major_aspects, minor_aspects)
    user_text= remove_punctuation_and_lower(user_text)
    conclusion_phrases = [
    "in summary", "ultimately", "consequently", "in conclusion", "to sum up", "overall", "therefore", "thus", "as a result", "taking everything into account",
    "in light of the evidence presented","given these points", "in essence", "summarizing the findings", "considering the implications", "finally", "hence", "reflecting on the main points", "from this analysis, we can conclude that", "the evidence strongly suggests that",
    "in hindsight", "to conclude", "in retrospect", "in a nutshell", "all things considered", "in the final analysis", "in the grand scheme of things", "to wrap things up", "in the end", "to summarize", "to bring everything together", "to draw a conclusion", "to close", "ultimately speaking", "in closing", "to cap it all off", "in the long run", "in summary", "to put it concisely", "in brief"
    ]

    conchecker = check_conclusion_phrases(user_text, conclusion_phrases)
    print("Con Checker::", conchecker)
    fluency_score, comments1 = calculate_fluency_score(apropriacy_score1, pauses, len(user_text.split()), duration, conchecker, speaking_duration)
    splitter(file)
    pronounciation_remarks, pronounciation_score = calculate_pronunciation_score()
    comments.extend(comments1)

    caps = [
        ((0, 40), 37),
        ((41, 45), 44),
        ((46, 50), 48),
        ((51, 55), 53),
        ((56, 60), 59),
        ((61, 65), 64),
        ((66, 70), 68),
        ((71, 75), 72),
        ((76, 80), 77),
        ((81, 85), 84),
        ((86, 90), 90),
    ]

    # Apply the cap on pronunciation
    for range_pair, max_pron in caps:
        lower, upper = range_pair
        if lower <= apropriacy_score1 <= upper:
            if pronounciation_score > max_pron:
                pronounciation_score = max_pron
            break

    print('Capped pronunciation score:', pronounciation_score)



    # Define the temporary directory where the split audio files are stored
    temp_dir = "splitter"

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio files
    audio_dir = os.path.join(script_dir, temp_dir)

    # Clean up the temporary directory by deleting all .wav and .TextGrid files
    for file_path in Path(audio_dir).glob("*.wav"):
        os.remove(file_path)

    for file_path in Path(audio_dir).glob("*.TextGrid"):
        os.remove(file_path)


    return apropriacy_score1, fluency_score, pronounciation_remarks, comments, pronounciation_score




def respondscoring1(user_text, major_aspects, minor_aspects):
    apropricay_score, comments = appropriacy_score(user_text, major_aspects, minor_aspects)
    fluency_score = 0.0
    pronounciation_score = 0.0


    return apropricay_score, fluency_score, pronounciation_score, comments
