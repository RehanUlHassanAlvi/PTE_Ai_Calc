import io
import os
from pathlib import Path
import string
import sys
import numpy as np
from pydub import AudioSegment

def calculate_content_score(correct_text, user_text):
    correct_words = correct_text.split()
    user_words = user_text.split()

    # Helper function to get word indices in a text
    def get_word_indices(text):
        words = text.split()
        indices = []
        current_position = 0
        for word in words:
            start_index = current_position
            end_index = start_index + len(word)
            indices.append((start_index, end_index))
            current_position = end_index + 1
        return words, indices

    correct_words, correct_indices = get_word_indices(correct_text)
    user_words, user_indices = get_word_indices(user_text)

    # Determine the longest common subsequence
    def longest_common_subsequence(X, Y):
        m = len(X)
        n = len(Y)
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

        # Reconstruct the LCS from the backtrack table
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

    # Determine correct and incorrect word indices
    correct_word_indices = []
    incorrect_word_indices = []
    missing_word_indices = []
    correct_word_positions = {j for _, j in lcs_indices}

    for idx, (start_index, end_index) in enumerate(user_indices):
        if idx in correct_word_positions:
            correct_word_indices.append([start_index, end_index])
        else:
            incorrect_word_indices.append([start_index, end_index])

    for idx, (start_index, end_index) in enumerate(correct_indices):
        if idx not in {i for i, _ in lcs_indices}:
            missing_word_indices.append([start_index, end_index])

    # Calculate content score
    correct_count = len(lcs_indices)
    total_words = len(correct_words)
    content_score = (correct_count / total_words) * 90

    correct_words_list = []

    # Add words using indices in correct words list array
    for start, end in correct_word_indices:
        word = user_text[start:end]
        correct_words_list.append(word)

    comments = []

    if content_score == 90:
        comments.append("Great content score!")
    elif 50 <= content_score <= 90:
        comments.append("Try to repeat more correct words to achieve better marks.")
    elif content_score <= 49:
        comments.append("Too few correct words are repeated.")

    return content_score, correct_word_indices, incorrect_word_indices, missing_word_indices, comments, correct_words_list



def calculate_fluency_score(content_score, number_of_pauses, number_of_words, duration, repeated_words, speaking_dur):
    print("Content Percentage::", content_score)
    print("Number of Pauses::", number_of_pauses)
    print("Number of Words::", number_of_words)
    print("duration::", duration)
    print("Repeated Words::", repeated_words)
    comments = []
    CONTENT_WEIGHT = 30
    PAUSE_WEIGHT = 30
    WPS_WEIGHT = 30
    REPETATION_WEIGHT=10
    PAUSE_COST = 5
    LONG_PAUSE_COST = 10

    words = int(number_of_words)
    dur = float(duration)
    wps = (words) / dur
    wps = round(wps, 2)
    print("Words Per Second::", wps)

    pauses = int(number_of_pauses)
    duration = float(duration)
    speaking_dur = float(speaking_dur)

    finalduration = duration - speaking_dur
    finalduration = round(finalduration, 2)
    print("Final Duration::", finalduration)


    # CORRECTION----------------------------------
    if pauses == 0:
        long_pause = 0
    else:
        long_pause = finalduration / pauses

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

    #repeated_words_penalty=(repeated_words/100)*10

    fluency_score=real_content_score+penalty_score+wps_score#-repeated_words_penalty
#on pauses and wps and fluency  <60 try to speak more

    if content_score > 50 and pauses <= 1 and wps >= 2.0 and repeated_words == 0:
        comments.append("Great Fluency.")
        comments.append("Words per Second Were in Acceptable Range.")


    elif content_score > 50 and pauses <= 2 and wps >= 1.75 and repeated_words <= 1:
        comments.append("Words per Second Were in Acceptable Range.")
        if pauses == 1:
            comments.append("One pause was detected in your audio.")
        if pauses > 1:
            comments.append("More than one pause was detected in your audio.")
        if repeated_words > 0:
            comments.append("Words are being repeated.")
        

    elif content_score >= 25 and pauses <= 4 and wps >= 1.75 and repeated_words <= 3:
        comments.append("Words per Second Were in Acceptable Range.")
        if content_score < 50:
            comments.append("Correct spoken content is less than 50%.")
        if pauses == 1:
            comments.append("One pause was detected in your audio.")
        if pauses > 1:
            comments.append("More than one pause was detected in your audio.")
        if repeated_words > 0:
            comments.append("Words are being repeated.")
        if long_pause > 3:
            comments.append("Long pause was detected.")


    elif content_score >= 25 and pauses <= 4 and wps >= 1.40 and repeated_words <= 3:
        comments.append("Words per Second Were Not in Acceptable Range.")
        if content_score <50:
            comments.append("Correct spoken content is less than 50%.")
        if pauses == 1:
            comments.append("One pause was detected in your audio.")
        if pauses > 1:
            comments.append("More than one pause was detected in your audio.")
        if repeated_words > 0:
            comments.append("Words are being repeated.")
        if long_pause > 3:
            comments.append("Long pause was detected.")


    elif content_score >= 5 and pauses <= 5 and wps >= 1.0 and repeated_words <= 5:
        comments.append("Words per Second Were Not in Acceptable Range.")
        if content_score < 50:
            comments.append("Correct spoken content is less than 50%.")
        if pauses == 1:
            comments.append("One pause was detected in your audio.")
        if pauses > 1:
            comments.append("More than one pause was detected in your audio.")
        if repeated_words > 0:
            comments.append("Words are being repeated.")
        if long_pause > 3:
            comments.append("Long pause was detected.")


    else:
        comments.append("Insufficient amount of Cont ent Said.")
        if pauses == 1:
            comments.append("One pause was detected in your audio.")
        if pauses > 1:
            comments.append("More than one pause was detected in your audio.")
        if repeated_words > 0:
            comments.append("Words are being repeated.")
        if wps < 1.2 or wps > 3:
            comments.append("Words per second out of expected range.")
        if long_pause > 3:
            comments.append("Long pause was detected.")

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



def calculate_pronounciation_score(contentScore):
    
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

    # print("AVG SCORE:::", avg_score)
    #
    # if 85 <= avg_score and contentScore>=2:
    #     score = 5.0
    # elif 65 <= avg_score < 85 and contentScore>=2:
    #     score = 4.0
    # elif 50 <= avg_score < 65 and contentScore>=2:
    #     score = 3.0
    # elif 25 <= avg_score < 50 and contentScore>=1:
    #     score = 2.0
    # elif 5 <= avg_score < 25 and contentScore>=1:
    #     score = 1.0
    # else:
    #     score = 0.0

    return pron_scores, score



def remove_punctuation_and_lower(text):
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()
    return cleaned_text


def repeatsentencescoring(correct_text, user_text, pauses, duration, repeated_words, speaking_dur, file):
    content_score, correct_word_indices, incorrect_word_indices, missing_word_indices, comments, correct_words_array = calculate_content_score(correct_text, user_text)
    fluency_score, comments1 = calculate_fluency_score(content_score, pauses, len(user_text.split()), duration, repeated_words, speaking_dur)
    
    splitter(file)
    pronounciation_score, pron_score = calculate_pronounciation_score(content_score)

    if content_score == 0:
        fluency_score = 0.0
        pronounciation_score = 0.0

    comments.extend(comments1)

    # difference_score = fluency_score - pron_score

    # print("Difference Score::", difference_score)
    #
    # if difference_score == 5.0:
    #     pron_score += 3.0
    # elif difference_score == 4.0:
    #     pron_score += 2.0
    # elif difference_score == 3.0:
    #     pron_score += 1.0
    # elif difference_score == -5.0:
    #     pron_score -= 3.0
    # elif difference_score == -4.0:
    #     pron_score -= 2.0
    # elif difference_score == -3.0:
    #     pron_score -= 1.0
    # else:
    #     pron_score += 0.0

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
            if pron_score > max_pron:
                pron_score = max_pron
            break

    print('Capped pronunciation score:', pron_score)

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

        
    return content_score, fluency_score, pronounciation_score, correct_word_indices, incorrect_word_indices, missing_word_indices, comments, pron_score, correct_words_array



def repeatsentencescoring1(correct_text, user_text):
    content_score, correct_word_indices, incorrect_word_indices, missing_word_indices, contenter, comments = calculate_content_score(correct_text, user_text)
    fluency_score = 0.0
    pronounciation_score = fluency_score

    if content_score == 0:
        fluency_score = 0.0
        pronounciation_score = 0.0


    print("Correct Text::", correct_text)
    print("User Text::", user_text)
    return content_score, fluency_score, pronounciation_score, correct_word_indices, incorrect_word_indices, missing_word_indices
 
