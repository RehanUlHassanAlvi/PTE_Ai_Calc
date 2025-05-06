import io
import os
from pathlib import Path
import sys
from pydub import AudioSegment
import numpy as np
import re

def remove_punctuation(text):
    return re.sub(r'[^\w\s]', '', text)


def calculate_content_score(correct_text, user_text):
    correct_text = remove_punctuation(correct_text)

    correct_words = correct_text.split()
    user_words = user_text.split()

    # Determine the longest common subsequence
    def longest_common_subsequence(X, Y):
        m, n = len(X), len(Y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        backtrack = [[None] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                    backtrack[i][j] = (i-1, j-1)
                else:
                    if L[i-1][j] >= L[i][j-1]:
                        L[i][j] = L[i-1][j]
                        backtrack[i][j] = (i-1, j)
                    else:
                        L[i][j] = L[i][j-1]
                        backtrack[i][j] = (i, j-1)

        i, j = m, n
        lcs = []
        while i > 0 and j > 0:
            if backtrack[i][j] == (i-1, j-1):
                lcs.append((i-1, j-1))
                i -= 1
                j -= 1
            elif backtrack[i][j] == (i-1, j):
                i -= 1
            else:
                j -= 1

        lcs.reverse()
        return lcs

    lcs_indices = longest_common_subsequence(correct_words, user_words)

    # Calculate error percentage
    correct_count = len(lcs_indices)
    total_words = len(correct_words)
    #no need for total_words ==> correct_count/totalwords
    content_score = (( correct_count) / total_words) * 90

    # Calculate correct and incorrect word indices
    correct_word_indices = []
    incorrect_word_indices = []
    correct_words_array = []

    user_index = 0
    for word in user_words:
        if word in correct_words:
            start_index = user_text.find(word, user_index)
            end_index = start_index + len(word)
            correct_word_indices.append((start_index, end_index))
            correct_words_array.append(word)
        else:
            start_index = user_text.find(word, user_index)
            end_index = start_index + len(word)
            incorrect_word_indices.append((start_index, end_index))
        user_index = end_index + 1

    return content_score, correct_word_indices, incorrect_word_indices, correct_words_array





def calculate_fluency_score(total_score, number_of_pauses, number_of_words, duration, speaking_duration, allowed_pauses):
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

    pauses = int(number_of_pauses)
    print(type(pauses))

    duration = float(duration)
    speaking_dur = float(speaking_duration)

    diffduration = duration - speaking_dur

    diffduration = round(diffduration,2)

    print("Difference Duration::", diffduration)

    pauses -= allowed_pauses

    pauses = max(0, pauses)
    print("Final Pauses::", pauses)
    #CORRECTION------------------------
    if pauses == 0:
        long_pause = 0
    else:
        long_pause = diffduration / pauses

    print("Long Pause::", long_pause)
    #long pause will be fixed later
    real_content_score = round((total_score / 90) * CONTENT_WEIGHT)
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

    # Construct the full path to the directory containing the audio files
    audio_dir = os.path.join(script_dir, temp_dir)
    
    # Iterate over all files in the specified directory
    for file_path in Path(audio_dir).glob("*.wav"):
        file_name = file_path.stem

        temp_path = os.path.join(audio_dir, file_name + '.wav')

        # Capture the output of mysp.mysptotal()
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            mysp.mysppron(file_name, audio_dir)
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")

        sys.stdout = sys.__stdout__  # Reset redirect

        # Process the captured output to extract the data
        output = captured_output.getvalue()

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
    # if 80 <= avg_score:
    #     score = 5.0
    # elif 65 <= avg_score < 80:
    #     score = 4.0
    # elif 50 <= avg_score < 65:
    #     score = 3.0
    # elif 30 <= avg_score < 50:
    #     score = 2.0
    # elif 5 <= avg_score < 30:
    #     score = 1.0
    # else:
    #     score = 0.0

    return pron_scores, score


def readaloudscoring(script, user_response, number_of_pauses, num_words, duration, speaing_duration, file):
    # Calculate the number of full stops in the script
    number_of_full_stops = script.count('.')

    content_score, correct_indices, incorrect_indices, correct_words_array = calculate_content_score(script, user_response)
    fluency_score, comments = calculate_fluency_score(content_score, number_of_pauses, num_words, duration, speaing_duration, number_of_full_stops)

    splitter(file)
    pronounciation_remarks, pronounciation_score = calculate_pronunciation_score()

    difference_score = fluency_score - pronounciation_score

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

    return content_score, 90, correct_indices, incorrect_indices, fluency_score, comments, pronounciation_remarks, pronounciation_score, correct_words_array


def readaloudscoring1(script, user_response):
    content_score, total_content_score= calculate_content_score(script, user_response)
    fluency_score = 0.0
    pronounciation_score = 0.0


    return content_score, fluency_score, pronounciation_score, total_content_score
