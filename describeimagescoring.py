
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
    
    print("N GRAM::", n_grams)
    # Count the occurrences of each n-gram
    n_gram_counts = Counter(all_n_grams)
    
    # Return the phrases that appear more than once and have at least 'n' words
    return {k: v for k, v in n_gram_counts.items() if v > 1 and len(k.split()) >= n}


def high_alert_phrase(user_text):

    skip_phrases1 = [
        'i can see a very informative picture', 'i can see a very informative image', 'can see a very informative image', 'can see a very informative picture'
    ]

    phrase_count = 0
    essay_lower = user_text.lower()  # Convert essay to lowercase for case-insensitive matching
    
    for phrase in skip_phrases1:
        phrase_lower = phrase.lower()
        count = 0
        
        # While the phrase exists in the essay, count and remove it
        while phrase_lower in essay_lower:
            count += 1
            start_index = essay_lower.index(phrase_lower)
            end_index = start_index + len(phrase_lower)
            # Remove the found phrase from the essay
            essay_lower = essay_lower[:start_index] + " " * len(phrase_lower) + essay_lower[end_index:]
        
        phrase_count += count

    return phrase_count


def content_score_image(user_text, major_aspect, minor_aspect):

    user_text = remove_punctuation_and_lower(user_text)

    phrases_to_check = ["i look from", "i looked from", "i also looked from", "i also look from", "i looked that", "i also looked that", "i also look that",
                    "i view from", "i viewed from", "i also viewed from", "i also view from", "i viewed that", "i also viewed that",
                    "i see from", "i saw from", "i also saw from", "i also see from", "i saw that", "i also saw that",
                    "i talk about", "i also talk about", "i talk about", "i looked about", "i also looked about", "i look about",
                    "i viewed about", "i also viewed about", "i view about", "i saw about", "i also saw about", "i see about",
                    "i observe from", "i observed from", "i also observed from", "i also observe from", "i observed that", "i also observed that",
                    "i witness from", "i witnessed from", "i also witnessed from", "i also witness from", "i witnessed that", "i also witnessed that",
                    "i notice from", "i noticed from", "i also noticed from", "i also notice from", "i noticed that", "i also noticed that",
                    "i examine from", "i examined from", "i also examined from", "i also examine from", "i examined that", "i also examined that",
                    "i read from", "i also read from", "i also read about", "i also read that"
                    ]

    skip_phrases1 = phrases_to_check + ["also look from", "also looked from", "also looked that","also look that", "i also see", "i also observe", "also witness from", "also witnessed from", "also witnessed that", 
    "i also examined", "I also examine", "also examine from", "also read from", "i also read", "i also notice", "also notice from", "also see from", "also saw that", "also saw from", "also examined that", "also examined from", "also examine from",
    "I can see", "I can also See", "I can see that", "I can see about"]

    num_occurrences = 0

    phrase_count = 0
    essay_lower = user_text.lower()  # Convert essay to lowercase for case-insensitive matching
    
    for phrase in skip_phrases1:
        phrase_lower = phrase.lower()
        count = 0
        
        # While the phrase exists in the essay, count and remove it
        while phrase_lower in essay_lower:
            count += 1
            start_index = essay_lower.index(phrase_lower)
            end_index = start_index + len(phrase_lower)
            # Remove the found phrase from the essay
            essay_lower = essay_lower[:start_index] + " " * len(phrase_lower) + essay_lower[end_index:]
        
        phrase_count += count

    
    high_alert_phrase_count = high_alert_phrase(user_text)

    recurring_phrases = find_recurring_phrases(user_text, n=3, skip_phrases=skip_phrases1)

    recurring_phrases1 = merge_phrases(recurring_phrases)

    count1 = len(recurring_phrases1)

    num_occurrences += count1

    # Split the user text into words/phrases for comparison
    user_text_words = set(user_text.lower().split())

    # Count the number of major aspects mentioned in the user text
    major_count = sum(1 for aspect_group in major_aspect if any(aspect.lower() in user_text.lower() for aspect in aspect_group))
    # Count the number of minor aspects mentioned in the user text
    minor_count = sum(1 for aspect_group in minor_aspect if any(aspect.lower() in user_text.lower() for aspect in aspect_group))
    comments= []

    content_score = (major_count / len(major_aspect)) * 60 + (minor_count / len(minor_aspect)) * 30

    if content_score > 0:
        occur_scale = max(0, 1 - 0.15 * max(num_occurrences - 1, 0))
        phrase_scale = max(0, 1 - 0.15 * max(phrase_count - 1, 0))
        high_alert_scale = max(0, 1 - 0.3 * max(high_alert_phrase_count - 1, 0))
        unique_word_scale = min(len(user_text_words) / 50, 1.0)

        content_score = content_score * phrase_scale* occur_scale * high_alert_scale * unique_word_scale

    # if(high_alert_phrase_count == 1):
    #     content_score = content_score - 30
    # elif high_alert_phrase_count >= 2:
    #     content_score = 0
    #
    # content_score = max(0, content_score - (phrase_count * 0.5))



    # Determine the content score based on the criteria
    if content_score == 90:
        comments.append("Great content score!")
    elif content_score == 70:
        comments.append("Try to give more correct description to achieve better marks.")
    elif content_score == 50:
        comments.append("Try to give more correct description to achieve better marks.")
    elif content_score <= 30:
        comments.append("A good answer for image description should include picture information, a comparison, and a conclusion.")


    return content_score, comments


def calculate_fluency_score_image(content_score, number_of_pauses, number_of_words, duration, conclusion_checker, speaking_duration):
    CONTENT_WEIGHT = 30
    PAUSE_WEIGHT = 30
    WPS_WEIGHT = 30

    PAUSE_COST = 5
    LONG_PAUSE_COST = 10

    comments = []

    words = int(number_of_words)
    dur = float(duration)
    wps = (words - 1) / dur
    wps = round(wps, 2)
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


    real_content_score = round((content_score / 90) * CONTENT_WEIGHT)
    penalty = (pauses * PAUSE_COST) + (long_pause * LONG_PAUSE_COST)
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


    #
    #
    # if fluency_score > 0.0 and pauses <= 15 and wps >= 1.0:
    #     comments.append("Words per Second Were Not in Acceptable Range.")
    #     comments.append("Insufficient Amount of Content was Said while describing Image.")
    #     if pauses == 1:
    #         comments.append("One pause was detected in your audio.")
    #     if pauses > 1:
    #         comments.append("More than one pause was detected in your audio.")
    #     if long_pause > 3:
    #         comments.append("Long pause was detected.")
    #     if not conclusion_checker:
    #         comments.append("Conclusion was missing from the content.")
    #
    #
    #
    # else:
    #     comments.append("Insufficient Amount of Content was Said while describing Image.")
    #     comments.append("Words per Second Were Not in Acceptable Range.")
    #     if pauses == 1:
    #         comments.append("One pause was detected in your audio.")
    #     if pauses > 1:
    #         comments.append("More than one pause was detected in your audio.")
    #     if not conclusion_checker:
    #         comments.append("Conclusion was missing from the content.")
    #     if long_pause > 3:
    #         comments.append("Long pause was detected.")



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

    # if 85 <= avg_score:
    #     score = 5.0
    # elif 65 <= avg_score < 85:
    #     score = 4.0
    # elif 50 <= avg_score < 65:
    #     score = 3.0
    # elif 25 <= avg_score < 50:
    #     score = 2.0
    # elif 5 <= avg_score < 25:
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


def describeimagescoring(user_text, major_aspects, minor_aspects, pauses, duration, speaking_duration, file):
    content_score, comments = content_score_image(user_text, major_aspects, minor_aspects)
    user_text= remove_punctuation_and_lower(user_text)
    conclusion_phrases = [
    "in summary", "ultimately", "consequently", "in conclusion", "to sum up", "overall", "therefore", "thus", "as a result", "taking everything into account",
    "in light of the evidence presented","given these points", "in essence", "summarizing the findings", "considering the implications", "finally", "hence", "reflecting on the main points", "from this analysis, we can conclude that", "the evidence strongly suggests that",
    "in hindsight", "to conclude", "in retrospect", "in a nutshell", "all things considered", "in the final analysis", "in the grand scheme of things", "to wrap things up", "in the end", "to summarize", "to bring everything together", "to draw a conclusion", "to close", "ultimately speaking", "in closing", "to cap it all off", "in the long run", "in summary", "to put it concisely", "in brief"
    ]

    conclusion_checker = check_conclusion_phrases(user_text, conclusion_phrases)
    print("Con Checker::", conclusion_checker)
    fluency_score, comments1 = calculate_fluency_score_image(content_score, pauses, len(user_text.split()), duration, True, speaking_duration)
    splitter(file)
    pronounciation_remarks, pronounciation_score = calculate_pronunciation_score()
    comments.extend(comments1)


    # difference_score = fluency_score - pronounciation_score
    #
    # print("Difference Score::", difference_score)
    #
    # if difference_score == 5.0:
    #     pronounciation_score += 3.0
    # elif difference_score == 4.0:
    #     pronounciation_score += 2.0
    # elif difference_score == 3.0:
    #     pronounciation_score += 1.0
    # elif difference_score == -5.0:
    #     pronounciation_score -= 3.0
    # elif difference_score == -4.0:
    #     pronounciation_score -= 2.0
    # elif difference_score == -3.0:
    #     pronounciation_score -= 1.0
    # else:
    #     pronounciation_score += 0.0

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

    # Apply the cap
    for range_pair, max_pron in caps:
        lower, upper = range_pair
        if lower <= content_score <= upper:
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


    return content_score, fluency_score, pronounciation_remarks, comments, pronounciation_score




def describeimagescoring1(user_text, major_aspects, minor_aspects):
    content_score, comments = content_score_image(user_text, major_aspects, minor_aspects)
    fluency_score = 0.0
    pronounciation_score = 0.0


    return content_score, fluency_score, pronounciation_score, comments
