import io
import os
from pathlib import Path
import re
import sys
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict
import numpy as np
from pydub import AudioSegment
import librosa
import soundfile as sf

def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)

# Download necessary NLTK data files
nltk.download('punkt')
nltk.download('stopwords')


def split_audio_on_silence(audio_path, output_dir, min_silence_len=0.11, silence_thresh=-40):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the audio file
    y, sr = librosa.load(audio_path, sr=None)

    # Detect silent intervals
    intervals = librosa.effects.split(y, top_db=silence_thresh, frame_length=int(sr * min_silence_len))

    # Export each detected segment
    for i, (start, end) in enumerate(intervals):
        chunk = y[start:end]
        out_file = os.path.join(output_dir, f"chunk{i+1}.wav")
        print("Exporting", out_file)
        sf.write(out_file, chunk, sr)


def calculate_word_count(text):
    words = text.split()
    return len(words)

def calculate_percentage(original_count, user_count):
    print("User Word Count::", user_count)
    print("Original Count::", original_count)
    return (user_count / original_count) * 100 if original_count > 0 else 0

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    filtered_words = [word for word in words if word.lower() not in stop_words and word.isalnum()]
    return filtered_words

def calculate_aspect_percentage(original_aspects, user_aspects):
    matched_aspects = [aspect for aspect in user_aspects if aspect in original_aspects]
    print("MATCHED ASPECTS:::", matched_aspects)
    return (len(matched_aspects) / len(original_aspects)) * 100 if len(original_aspects) > 0 else 0


def calculate_matched_aspects(original_aspects, user_aspects):
    matched_aspects = [aspect for aspect in user_aspects if aspect in original_aspects]
    print("MATCHED ASPECTS:::", matched_aspects)
    return len(matched_aspects)

# Conclusion Check Function
def check_conclusion(user_response):
    conclusion_phrases = [
    "in summary", "ultimately", "consequently", "in conclusion", "to sum up", "overall", "therefore", "thus", "as a result", "taking everything into account",
    "in light of the evidence presented","given these points", "in essence", "summarizing the findings", "considering the implications", "finally", "hence", "reflecting on the main points", "from this analysis, we can conclude that", "the evidence strongly suggests that",
    "in hindsight", "to conclude", "in retrospect", "in a nutshell", "all things considered", "in the final analysis", "in the grand scheme of things", "to wrap things up", "in the end", "to summarize", "to bring everything together", "to draw a conclusion", "to close", "ultimately speaking", "in closing", "to cap it all off", "in the long run", "in summary", "to put it concisely", "in brief"
    ]
    return any(phrase in user_response.lower() for phrase in conclusion_phrases)


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


def check_repeated_phrases(user_response):

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

    phrase_count = 0
    essay_lower = user_response.lower()  # Convert essay to lowercase for case-insensitive matching
    
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

    return phrase_count, skip_phrases1


def contentscoring(script, user_response):
    # Step 1: Word Count Comparison
    script_word_count = calculate_word_count(script)
    user_response_word_count = calculate_word_count(user_response)
    word_percentage = calculate_percentage(script_word_count, user_response_word_count)

    
    # Step 2: Aspect Identification
    original_aspects = remove_stopwords(script)
    user_aspects = remove_stopwords(user_response)


    aspect_percentage = calculate_aspect_percentage(original_aspects, user_aspects)

    # Matched Aspects
    matched_ascpects = calculate_matched_aspects(original_aspects, user_aspects)
    
    # Step 3: Conclusion Check
    # conclusion_present = check_conclusion(user_response)
    conclusion_present = True
        
    # Step 4: Repeated Phrases Check
    repetition_count, skip_phrases1 = check_repeated_phrases(user_response)

    recurring_phrases = find_recurring_phrases(user_response, n=3, skip_phrases=skip_phrases1)

    recurring_phrases1 = merge_phrases(recurring_phrases)

    num_occourances = len(recurring_phrases1)

    # repetition_count += count1

    correct_word_indices = []
    incorrect_word_indices = []
    correct_words_list = []

    correct_words = script.split()
    user_words = user_response.split()

    user_response= remove_punctuation(user_response)
    script = remove_punctuation(script)

    user_index = 0
    for word in user_words:
        if word in correct_words:
            start_index = user_response.find(word, user_index)
            end_index = start_index + len(word)
            correct_word_indices.append((start_index, end_index))
            correct_words_list.append(word)
        else:
            start_index = user_response.find(word, user_index)
            end_index = start_index + len(word)
            incorrect_word_indices.append((start_index, end_index))
        user_index = end_index + 1  # Update index to search for the next word correctly


    # Scoring
    content_score = (matched_ascpects / 15) * 90

    # if conclusion_present and matched_ascpects > 15 and user_response_word_count >= 50:
    #     score = 5.0
    #
    # elif conclusion_present and matched_ascpects >=11 and user_response_word_count >= 45:
    #     score = 4.0
    #
    # elif conclusion_present and matched_ascpects >=8 and user_response_word_count >= 40:
    #     score = 3.0
    #
    # elif user_response_word_count >= 35 and matched_ascpects > 5:
    #     score = 2.0
    #
    # elif user_response_word_count >= 30 and matched_ascpects > 1:
    #     score = 1.0
    #
    # else:
    #     score = 0.0
    #
    # score = max(0, score - (repetition_count * 0.5))

    if content_score > 0:
        # Apply repetition penalty (each extra repetition over 1, lose 15%)
        repetition_factor = max(0, 1 - 0.15 * (repetition_count - 1))
        num_occourances_scale=max(0, 1 - 0.15 * (num_occourances - 1))
        # Unique words scaling (if user_word_count >= 50, this is 1; if less, scales down)
        unique_words_scale = min(user_response_word_count / 50, 1.0)

        # Apply both scaling factors
        content_score = content_score * repetition_factor * unique_words_scale * num_occourances_scale

    return content_score, correct_word_indices, incorrect_word_indices, correct_words_list



def calculate_fluency_score(content_score, number_of_pauses, number_of_words, duration, speaking_duration):

    CONTENT_WEIGHT = 30
    PAUSE_WEIGHT = 30
    WPS_WEIGHT = 30
    PAUSE_COST=5

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

    #CORRECTION------------------------
    # if pauses == 0:
    #     long_pause = 0
    # else:
    #     long_pause = diffduration / pauses

    real_content_score = round((content_score / 90) * CONTENT_WEIGHT)
    penalty = (pauses * PAUSE_COST) #+ (long_pause * LONG_PAUSE_COST)
    penalty_score = PAUSE_WEIGHT - penalty

    if 2.0 <= wps < 2.5:
        wps_score = WPS_WEIGHT
    elif 1.75 <= wps < 2.75:
        wps_score = WPS_WEIGHT - 10
    elif 1.65 <= wps < 2.85:
        wps_score = WPS_WEIGHT - 20
    else:
        wps_score = 0

    fluency_score = real_content_score + penalty_score + wps_score

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
        elif pron_score >= 40:
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

    # print("AVG SCORE:::", avg_score)
    #
    # if 85 <= avg_score:
    #     score = 90
    # elif 65 <= avg_score < 85:
    #     score = 70
    # elif 50 <= avg_score < 65:
    #     score = 50
    # elif 25 <= avg_score < 50:
    #     score = 40
    # elif 5 <= avg_score < 25:
    #     score = 30
    # else:
    #     score = 0.0

    return pron_scores, score


def retellecturescoring(script, user_response, number_of_pauses, num_words, duration, speaing_duration, file):
    content_score, correct_indices, incorrect_indices, correct_words_list = contentscoring(script, user_response)
    fluency_score, comments = calculate_fluency_score(content_score, number_of_pauses, num_words, duration, speaing_duration)


    print("FILEE", file)
    splitter(file)
    # output_dir = "splitter"
    # split_audio_on_silence(file, output_dir)
    pronounciation_remarks, pronounciation_score = calculate_pronunciation_score()

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

    return content_score, fluency_score, comments, pronounciation_remarks, pronounciation_score, correct_indices, incorrect_indices, correct_words_list


def retellecturescoring1(script, user_response):
    content_score, correct , incorrect = contentscoring(script, user_response)
    fluency_score = 0.0
    pronounciation_score = 0.0


    return content_score, fluency_score, pronounciation_score
