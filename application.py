import io
import json
import os
import sys
from flask import Flask, logging, request, jsonify
from flask_cors import CORS
from respond import respondscoring, respondscoring1
from answershortquestion import answershort
from readaloudscoring import readaloudscoring, readaloudscoring1
from retellecturescoring import retellecturescoring, retellecturescoring1
from helper_functions.fluencyscorehelper import compare_word_frequencies, word_frequencies
from describeimagescoring import describeimagescoring, describeimagescoring1
from repeatsentencescoring import remove_punctuation_and_lower, repeatsentencescoring, repeatsentencescoring1
from summarizespokensummary import summarizespoken_summary
from writedictationscoring import writedictationscoring
from summary_scoring import score_summary
from essay_scoring import score_essay
from accent_deduction import identify_accent
from email_scoring import score_email
from summary_scoring import count_sentences
from openai_tes import get_response_from_openai
from aws_bedrock_model import get_response_from_claude

application = Flask(__name__)
CORS(application, origins=[
    r"https://.*\.swiftuni\.com",
    "http://localhost:3000",
    "http://localhost:3002"
])

@application.route('/')
def home():
    return "Welcome to the pte ai scoring app! version 1.2.7"



@application.route('/summary', methods=['POST'])
def summary_endpoint():
    data = request.json
    passage = data['passage']
    summary = data['summary']
    pte_type= data['pte_type']


    # print("SUMMARYYYYY", summary)
    if pte_type=="pte academic":
        # Counting Number of Sentences in our Summary
        sen_num=count_sentences(summary)
        print("Number of sentences", sen_num)

        words = summary.split()  # Splits the summary into individual words
        num_words = len(words)  # Gets the total count of words
        print("Number of words:", num_words)

        # If sentences greater than 1 return 0 for all
        if sen_num > 1 :
            total_score=0
            content_score=0
            grammar_score=0
            form_score=0
            vocab_range_score=0
            spell_errors= []
            misspelled_indices= []
            grammar_errors=[]
            grammatical_indices=[]
            accent = identify_accent(summary)
            comments={}
            comments['Content']= ' Your response has to be in ONE single, complete sentence only. If this criterion is not met, you won’t get a score in rest of the enabling skills.'



        # If empty response send assign score of 0 to all
        elif num_words == 0 :
            total_score=0
            content_score=0
            grammar_score=0
            form_score=0
            vocab_range_score=0
            spell_errors= []
            misspelled_indices= []
            grammar_errors=[]
            grammatical_indices=[]
            accent = identify_accent(summary)
            comments={}
            comments['Content']= ' Your response should not be empty.'

        # OTHERWISE
        else:
            summary = summary.replace('\n', '')
            accent = identify_accent(summary)
            total_score,content_score, grammar_score, form_score, vocab_range_score, comments, spell_errors, grammar_errors, misspelled_indices, grammatical_indices = score_summary(passage, summary, pte_type, accent)

        # temp_mistakes =  get_response_from_openai(summary)        
        temp_mistakes = {"mistakes":[]}        
        mistakes = []  
        mistakes_list = []
        spelling_mistakes_list = []

        if grammar_score != 0:
            grammar_score = 2 - 0.5 * len(mistakes_list) if len(mistakes_list) > 4 else 0

        response = jsonify(
            {'accent': accent, 
            'total_score': total_score,
            'content_score': content_score,
            'grammar_score':  grammar_score,
            'form_score':form_score,
            'vocab_range_score':  vocab_range_score,
            'comments': comments,
            'corrected words': spell_errors,
            'misspelled words indices':misspelled_indices,
            'grammatical Mistakes': grammar_errors,
            'grammatical mistakes indices': grammatical_indices,
            "mistakes" : mistakes_list,
            "spelling_mistakes": spelling_mistakes_list,
             "temp_mistakes": temp_mistakes
            })

        return response
    

    elif pte_type=="pte core":
        # Counting Number of Sentences in our Summary
        sen_num=count_sentences(summary)

        words = summary.split()  # Splits the summary into individual words
        num_words = len(words)  # Gets the total count of words

        # If empty response send assign score of 0 to all
        if num_words == 0 :
            total_score=0
            content_score=0
            grammar_score=0
            form_score=0
            vocab_range_score=0
            spell_errors= []
            misspelled_indices= []
            grammar_errors=[]
            grammatical_indices=[]
            accent = identify_accent(summary)
            comments={}
            comments['Content']= ' Your response should not be empty.'
        
        else:
            summary = summary.replace('\n', '')
            accent = identify_accent(summary)
            total_score,content_score, grammar_score, form_score,vocab_range_score, comments, spell_errors, grammar_errors, misspelled_indices, grammatical_indices = score_summary(passage, summary, pte_type, accent)
        
        # temp_mistakes =  get_response_from_openai(summary)
        temp_mistakes = {"mistakes":[]}
        mistakes = []  
        mistakes_list = []
        spelling_mistakes_list = []
        
        if grammar_score != 0:
            grammar_score = 2 - 0.5 * len(mistakes_list) if len(mistakes_list) > 4 else 0

        response = jsonify(
            {'accent': accent, 
            'total_score': total_score,
            'content_score': content_score,
            'grammar_score':  grammar_score,
            'form_score': form_score,
            'vocab_range_score':  vocab_range_score,
            'comments': comments,
            'corrected words': spell_errors,
            'misspelled words indices': misspelled_indices,
            'grammatical mistakes': grammar_errors,
            'grammatical mistakes indices': grammatical_indices,     
            "mistakes" : mistakes_list,
            "spelling_mistakes": spelling_mistakes_list,
             "temp_mistakes": temp_mistakes
            })
        print(response)
        return response
             
    else:
        print("PTE ERROR OCCURED")
        return jsonify({'error': 'You have entered wrong pte type'}), 400



@application.route('/email', methods=['POST'])
def email_endpoint():
    try:
        data = request.json
        desc = data['desc']
        email = data['email']
        email = email.replace('\n\n', '\n')        
        major_aspects= data['major_aspect']
        minor_aspects= data['minor_aspect']

        print("major Aspects::", major_aspects)
        print("minor Aspects::", minor_aspects)

        # sentences,accent,index=check_accent(email)
        accent1= identify_accent(email)
        print("accent: ",accent1)
        content_score, grammar_score, vocab_range_score, spelling_score, form_score, organization_score, total_score, correct_words, comments, grammar_mistakes, misspelled_indices, grammtical_indices, email_convention_score = score_email(email, desc ,major_aspects ,minor_aspects ,accent1)

        # temp_mistakes =  get_response_from_openai(summary)
        temp_mistakes = {"mistakes":[]}
        mistakes = []  
        mistakes_list = []
        spelling_mistakes_list = []

        
        grammar_score = 2 - 0.5 * len(mistakes_list) if len(mistakes_list) > 4 else 0
        # (max_score - each_mistake * total_mistakes)


        response = jsonify({
            'total_score': total_score,
            'content_score': content_score,
            'grammar_score': grammar_score,
            'spelling_score': spelling_score,
            'form_score': form_score,
            'organization_score': organization_score,
            'vocab_range_score': vocab_range_score,
            'corrected words': correct_words,
            'comments': comments,
            'accent': accent1,
            'grammar mistakes': grammar_mistakes,
            'misspelled Indices': misspelled_indices,
            'grammatical mistakes indices': grammtical_indices,
            'email_convention_score': email_convention_score,
            'mistakes' : mistakes_list,
            'spelling_mistakes': spelling_mistakes_list,
            "temp_mistakes": temp_mistakes
        })
        print(response)
        return response
    except Exception as e:
        print("Error: ", e)
        return jsonify({'error': str(e)}), 500



@application.route('/write_dictation', methods=['POST'])
def writedictation_endpoint():
    data = request.json
    correct_answer = data['correct_answer']
    user_response = data['user_response']
    

    print("Correct Answer::", correct_answer)
    print("User Response::", user_response)

    # sentences,accent,index=check_accent(email)
    accent1= identify_accent(correct_answer)
    print("accent: ",accent1)

    words = correct_answer.split()  
    num_words = len(words) 
    print("Number of words:", num_words)
    

    score, matching_indices, correct_words, incorrect_indices, incorrect_words, missed_words, missed_word_indices= writedictationscoring(correct_answer,user_response,num_words)


    return jsonify({
        'total_score': num_words,
        'accent': accent1,
        'writing_score': score,
        'matching_indices': matching_indices,
        'correct_words': correct_words,
        'incorrect_indices': incorrect_indices,
        'incorrect_words': incorrect_words,
        'missed_words': missed_words,
        'missed_words_indices': missed_word_indices
    })


@application.route('/repeatsentence', methods=['POST'])
def repeatsentence():
    mysp = __import__("my-voice-analysis")
    
    print("Starting RS ----------------------------------------------------")

    # Ensure the 'audiofile' is in the request files
    if 'audiofile' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['audiofile']
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Fetch correct_text and user_text from form-data
    correct_text = request.form.get('correct_text', '')
    user_text = request.form.get('user_text', '')

    correct_text = remove_punctuation_and_lower(correct_text)
    user_text = remove_punctuation_and_lower(user_text)
    
    if not user_text:
        print("No user text")
        return jsonify({
                'content_score': 0.0,
                'fluency_score': 0.0,
                'pronunciation_score': 0.0,
                'comment': 'Kindly provide the content to get a score.'
            })
        
    # Save the uploaded file temporarily
    # temp_dir = r"C:\Users\ADMIN\Desktop\MYSP2"
    temp_dir = "audios"

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio file
    audio_dir = os.path.join(script_dir, temp_dir)
    # print("SCRIPT2222::", audio_dir)

    temp_path = os.path.join(audio_dir, file.filename)

    file.save(temp_path)
    # Redirect stdout to capture print statements
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        mysp.mysppron(file.filename.split('.')[0], audio_dir)
        mysp.mysptotal(file.filename.split('.')[0], audio_dir)
        sys.stdout = sys.__stdout__  # Reset redirect.
        output = captured_output.getvalue()
        
        # Process the captured output to extract the data
        output_lines = output.strip().split('\n')
        data = {}
        for line in output_lines:
            if line.strip():  # Ignore empty lines
                parts = line.split(maxsplit=1)
                if len(parts) == 2:  # Only process lines that can be split into exactly two parts
                    key, value = parts
                    if key.strip() == 'number_':
                        key = 'number_of_syllables'
                        value = value.replace('of_syllables ', '')
                    data[key.strip()] = value.strip()

        # Add word frequency comparison to the response
        correct_word_freq = word_frequencies(correct_text)
        user_word_freq = word_frequencies(user_text)
        repeated_words_difference, total_positive_difference = compare_word_frequencies(correct_word_freq, user_word_freq)

        # Check if 'number_of_pauses' exists in the data dictionary
        if 'number_of_pauses' in data:
            pauses = data['number_of_pauses']
            duration = data['original_duration']
            speaking_dur = data['speaking_duration']
            content_score, fluency_score, pronounciation_score, correct_word_indices, incorrect_word_indices, missing_word_indices, comments, pron_score, correct_words_array = repeatsentencescoring(correct_text, user_text, pauses, duration, total_positive_difference, speaking_dur, file)

            print("Finishing RS1 ----------------------------------------------------")

            if content_score == 0:
                fluency_score = 0
                pron_score = 0

            return jsonify({
                'number_of_pauses': data['number_of_pauses'],
                'original_duration': data['original_duration'],
                'rate_of_speech': data['rate_of_speech'],
                'speaking_duration': data['speaking_duration'],
                'content_score': content_score,
                'fluency_score': fluency_score,
                'pronunciation_score': pron_score,
                'correct_word_indices': correct_word_indices,
                'incorrect_word_indices': incorrect_word_indices,
                'missing_word_indices': missing_word_indices,
                'comments' : comments,
                'pronounciation_remarks': pronounciation_score,
                'correct_words': correct_words_array
            })
        else:
            # Handle the case where 'number_of_pauses' is not present
            content_score, fluency_score, pronounciation_score, correct_word_indices, incorrect_word_indices, missing_word_indices = repeatsentencescoring1(correct_text, user_text)
            fluency_score = 1.0
            pronounciation_score = 1.0
            print("Finishing RS2 ----------------------------------------------------")            
            return jsonify({
                'content_score': content_score,
                'fluency_score': fluency_score,
                'pronunciation_score': pronounciation_score,
                'correct_word_indices': correct_word_indices,
                'incorrect_word_indices': incorrect_word_indices,
                'missing_word_indices': missing_word_indices,
                'comment': 'The sound of the audio wasnt clear.'
            })

    except Exception as e:
        sys.stdout = sys.__stdout__  # Reset redirect on exception.
        # logging.error(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        sys.stdout = sys.__stdout__

   
@application.route('/describeimage', methods=['POST'])
def describeimage():
    mysp = __import__("my-voice-analysis")
    print("Starting DI ----------------------------------------------------")    
    # Ensure the 'audiofile' is in the request files
    if 'audiofile' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['audiofile']
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Fetch user_text from form-data
    user_text = request.form.get('user_text', '')

    # Fetch major_aspects and minor_aspects from form-data and parse them into lists
    major_aspects_str = request.form.get('major_aspects', '[]')
    minor_aspects_str = request.form.get('minor_aspects', '[]')

    try:
        major_aspects = json.loads(major_aspects_str)  # Use json.loads for JSON encoded strings
        minor_aspects = json.loads(minor_aspects_str)  # Use json.loads for JSON encoded strings
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid format for aspects"}), 400
    

    # Check if required fields are present
    if not major_aspects or not minor_aspects or not user_text:
        print("Finishing DI0 ----------------------------------------------------")
        return jsonify({
                'content_score': 0.0,
                'fluency_score': 0.0,
                'pronunciation_score': 0.0,
                'comment': 'Kindly provide the content to get a score.'
            })
  
        
    # Save the uploaded file temporarily

    temp_dir = "audios"


    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the directory containing the audio file
    audio_dir = os.path.join(script_dir, temp_dir)
    print("SCRIPT2222::", audio_dir)

    temp_path = os.path.join(audio_dir, file.filename)
    print("SCRIPT2222555::", temp_path)
    file.save(temp_path)
    # Redirect stdout to capture print statements
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        mysp.mysptotal(file.filename.split('.')[0], audio_dir)
        sys.stdout = sys.__stdout__  # Reset redirect.
        output = captured_output.getvalue()
        
        # Process the captured output to extract the data
        output_lines = output.strip().split('\n')
        data = {}
        for line in output_lines:
            if line.strip():  # Ignore empty lines
                parts = line.split(maxsplit=1)
                if len(parts) == 2:  # Only process lines that can be split into exactly two parts
                    key, value = parts
                    if key.strip() == 'number_':
                        key = 'number_of_syllables'
                        value = value.replace('of_syllables ', '')
                    data[key.strip()] = value.strip()

        # Remove the temporary file after processing
        # os.remove(temp_path)
        print("DATA::", data)
        # content_score, fluency_score, pronounciation_score, correct_word_indices = repeatsentencescoring(correct_text, user_text)
        # Check if 'number_of_pauses' exists in the data dictionary
        if 'number_of_pauses' in data:
            pauses = data['number_of_pauses']
            duration = data['original_duration']
            speaking_dur = data['speaking_duration']
            content_score, fluency_score, pronounciation_remarks, comments, pronounciation_score = describeimagescoring(user_text, major_aspects, minor_aspects, pauses, duration, speaking_dur, file)

            if content_score == 0:
                fluency_score = 0
                pronounciation_score = 0

            print("Ending DI1 ----------------------------------------------------")                

            return jsonify({
                'number_of_pauses': data['number_of_pauses'],
                'original_duration': data['original_duration'],
                'rate_of_speech': data['rate_of_speech'],
                'speaking_duration': data['speaking_duration'],
                'content_score': content_score,
                'fluency_score': fluency_score,
                'pronounciation_remarks': pronounciation_remarks,
                'pronounciation_score': pronounciation_score,
                'comments': comments
            })
        else:
            # Handle the case where 'number_of_pauses' is not present
            comments1 = 'The sound of the audio wasnt clear.'
            content_score, fluency_score, pronounciation_score, comments = describeimagescoring1(user_text, major_aspects, minor_aspects)
            comments.append(comments1)
            print("Ending DI2 ----------------------------------------------------")            
            return jsonify({
                'content_score': content_score,
                'fluency_score': fluency_score,
                'pronunciation_score': pronounciation_score,
                'comments': comments
            })

    except Exception as e:
        sys.stdout = sys.__stdout__  # Reset redirect on exception.
        # logging.error(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        sys.stdout = sys.__stdout__


@application.route('/summarizespoken', methods=['POST'])
def summarizespoken_endpoint():
    data = request.json
    passage = data['passage']
    summary = data['summary']
    pte_type= data['pte_type']


    # print("SUMMARYYYYY", summary)
    if pte_type=="pte academic":
        # Counting Number of Sentences in our Summary
        sen_num=count_sentences(summary)
        print("Number of sentences", sen_num)

        words = summary.split()  # Splits the summary into individual words
        num_words = len(words)  # Gets the total count of words
        print("Number of words:", num_words)

        # If empty response send assign score of 0 to all
        if num_words == 0 :
            total_score=0
            content_score=0
            grammar_score=0
            form_score=0
            vocab_range_score=0
            spell_errors= []
            misspelled_indices= []
            grammar_errors=[]
            grammatical_indices=[]
            accent = identify_accent(summary)
            comments={}
            comments['Content']= ' Your response should not be empty.'

        # OTHERWISE
        else:
            # temp=summary.split('.')
            # summary=temp[0]
            summary = summary.replace('\n', '')
            accent = identify_accent(summary)
            total_score,content_score, grammar_score, form_score, vocab_range_score, comments, spell_errors, grammar_errors, misspelled_indices, grammatical_indices, correct_words, spelling_score = summarizespoken_summary(passage, summary, pte_type, accent)


        temp_mistakes =  get_response_from_openai(summary)        
        mistakes = get_response_from_claude(summary)
        mistakes_list = mistakes.get("mistakes", []) 
        spelling_mistakes_list = mistakes.get("spelling_mistakes", [])

        if grammar_score != 0:
            grammar_score = 2 - 0.5 * len(mistakes_list) if len(mistakes_list) > 4 else 0

        # (max_score - each_mistake * total_mistakes)
               
                
        response = jsonify(
            {'accent': accent, 
            'total_score': total_score,
            'content_score': content_score,
            'grammar_score':  grammar_score,
            'form_score':form_score,
            'vocab_range_score':  vocab_range_score,
            'comments': comments,
            'corrected words': spell_errors,
            'misspelled words indices':misspelled_indices,
            'grammatical Mistakes': grammar_errors,
            'grammatical mistakes indices': grammatical_indices,
            'spelling_score': spelling_score,
            "mistakes" : mistakes_list,
            "spelling_mistakes": spelling_mistakes_list,
            "temp_mistakes": temp_mistakes
            })
        print(response)
        return response
    

    elif pte_type=="pte core":
        # Counting Number of Sentences in our Summary
        sen_num=count_sentences(summary)
        print("Number of sentences", sen_num)

        words = summary.split()  # Splits the summary into individual words
        num_words = len(words)  # Gets the total count of words
        print("Number of words:", num_words)

        # If empty response send assign score of 0 to all
        if num_words == 0 :
            total_score=0
            content_score=0
            grammar_score=0
            form_score=0
            vocab_range_score=0
            spell_errors= []
            misspelled_indices= []
            grammar_errors=[]
            grammatical_indices=[]
            accent = identify_accent(summary)
            comments={}
            comments['Content']= ' Your response should not be empty.'
        

        else:
            summary = summary.replace('\n', '')
            accent = identify_accent(summary)
            total_score,content_score, grammar_score, form_score, vocab_range_score, comments, spell_errors, grammar_errors, misspelled_indices, grammatical_indices, correct_words, spelling_score = summarizespoken_summary(passage, summary, pte_type, accent)
        

        temp_mistakes =  get_response_from_openai(summary) 
        mistakes = get_response_from_claude(summary)
        mistakes_list = mistakes.get("mistakes", []) 
        spelling_mistakes_list = mistakes.get("spelling_mistakes", [])

        if grammar_score != 0:
            grammar_score = 2 - 0.5 * len(mistakes_list) if len(mistakes_list) > 4 else 0

        response = jsonify(
            {'accent': accent, 
            'total_score': total_score,
            'content_score': content_score,
            'grammar_score':  grammar_score,
            'form_score':form_score,
            'vocab_range_score':  vocab_range_score,
            'comments': comments,
            'corrected words': spell_errors,
            'misspelled words indices':misspelled_indices,
            'grammatical mistakes': grammar_errors,
            'grammatical mistakes indices': grammatical_indices,
            'spelling_score': spelling_score,
            'temp_mistakes': temp_mistakes
            })        
        print(response)
        return response
             
    else:
        print("PTE ERROR OCCURED")
        return jsonify({'error': 'You have entered wrong pte type'}), 400


@application.route('/mistakes_detection', methods=['POST'])
def mistakes_detection():
    """
    Expected Input
    - {"text_paragraph" : "Text}

    Return
    {
        "mistakes" : [{
            "mistake_str": 'actual mistake string/sentence in the input for reference.,
            "mistake_explanation": 'Explain mistake and suggest solution in a single sentence (Mistake type).',
            "mistake_word": 'Mistake word/sequence'
        }]
    }
    """
    try:
        data = request.get_json()
        
        text_paragraph = data.get("text_paragraph", None)

        if text_paragraph is None:
            return jsonify({"error": "No text paragraph provided"}), 400
        
        print("\n/mistakes_detection")

        response = get_response_from_claude(text_paragraph)

        return jsonify({"mistakes": response.get('mistakes')})
    
    except Exception as e:
        print("Error: ", str(e))
        return jsonify({"error": str(e)}), 500


@application.route('/retellecture', methods=['POST'])
def retellecture():

    mysp = __import__("my-voice-analysis")

    print("Starting RL ----------------------------------------------------")

    # Ensure the 'audiofile' is in the request files
    if 'audiofile' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['audiofile']
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Fetch user_text from form-data
    user_response = request.form.get('user_response', '')

    # Fetch script from form-data
    script = request.form.get('script', '')


    words = script.split()  # Splits the script into individual words


    words1= user_response.split()
    num_words = len(words1)  # Gets the total count of words
    print("Number of words:", num_words)

    # Save the uploaded file temporarily
    # temp_dir = r"C:\Users\ADMIN\Desktop\MYSP2"
    temp_dir = "audios"


    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio file
    audio_dir = os.path.join(script_dir, temp_dir)
    print("SCRIPT2222::", audio_dir)

    temp_path = os.path.join(audio_dir, file.filename)
    print("SCRIPT2222555::", temp_path)
    file.save(temp_path)

    # Redirect stdout to capture print statements
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        mysp.mysptotal(file.filename.split('.')[0], audio_dir)
        sys.stdout = sys.__stdout__  # Reset redirect.
        output = captured_output.getvalue()
        
        # Process the captured output to extract the data
        output_lines = output.strip().split('\n')
        data = {}
        for line in output_lines:
            if line.strip():  # Ignore empty lines
                parts = line.split(maxsplit=1)
                if len(parts) == 2:  # Only process lines that can be split into exactly two parts
                    key, value = parts
                    if key.strip() == 'number_':
                        key = 'number_of_syllables'
                        value = value.replace('of_syllables ', '')
                    data[key.strip()] = value.strip()

        # Remove the temporary file after processing
        # os.remove(temp_path)
        print("DATA::", data)

        # If empty response send assign score of 0 to all
        if num_words == 0 :
            content_score=0
            comments={}
            comments['Content']= ' Your response should not be empty.'

            content_score = 0.0
            pronounciation_score = 0.0
            fluency_score = 0.0

            print("Finishing RL1 ----------------------------------------------------")            
            response = jsonify({ 
                'content_score': content_score,
                'pronounciation_score': pronounciation_score,
                'fluency_score': fluency_score,
                'comment': comments}) 
        
            return response

        # OTHERWISE IF WORDS ARE MORE THAN 0
        else:
            # temp=summary.split('.')
            # summary=temp[0]
            script = script.replace('\n', '')
            if 'number_of_pauses' in data:
                pauses = data['number_of_pauses']
                duration = data['original_duration']
                speaking_dur = data['speaking_duration']
                content_score, fluency_score, comments, pronounciation_remarks, pronounciation_score, correct_indices, incorrect_indices, correct_words_list = retellecturescoring(script, user_response, pauses, num_words, duration, speaking_dur, file)

                if isinstance(content_score, int) and content_score < 3:
                    if isinstance(fluency_score, int) and fluency_score >= 3:
                        fluency_score = 2

                if content_score == 0:
                    fluency_score = 0
                    pronounciation_score = 0                                

                response = jsonify({ 
                    'content_score': content_score,
                    'pronounciation_score': pronounciation_score,
                    'fluency_score': fluency_score,
                    'comments': comments,
                    'pronounciation_score': pronounciation_score,
                    'pronounciation_remarks': pronounciation_remarks,
                    'correct_indices': correct_indices,
                    'incorrect_indices': incorrect_indices,
                    'correct_words_list': correct_words_list})    
                print(response)
                print("Finishing RL2 ----------------------------------------------------")                
                return response
            else:
                # Handle the case where 'number_of_pauses' is not present
                comments1 = 'The sound of the audio wasnt clear.'
                content_score, fluency_score, pronounciation_score, correct, incorrect = retellecturescoring1(script, user_response)
                print("Finishing RL3 ----------------------------------------------------")                
                return jsonify({
                    'content_score': content_score,
                    'fluency_score': fluency_score,
                    'pronunciation_score': pronounciation_score,
                    'comments': comments1
                })
            

    except Exception as e:
        sys.stdout = sys.__stdout__  # Reset redirect on exception.
        # logging.error(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


# ----------------------- READ ALOUD SCORING ----------------------------------------------
@application.route('/readaloud', methods=['POST'])
def readaloud():
    mysp = __import__("my-voice-analysis")

    print("Starting RA ----------------------------------------------------")

    usermail = request.form.get('usermail', None)
    
    if usermail:
        print(f"User email: {usermail}")
    else:
        print("No user email provided.")

    # Ensure the 'audiofile' is in the request files
    if 'audiofile' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['audiofile']
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Fetch user_text from form-data
    user_response = request.form.get('user_response', '')

    # Fetch script from form-data
    script = request.form.get('script', '')


    words = user_response.split()  # Splits the user response into individual words
    num_words = len(words)  # Gets the total count of words

    # Save the uploaded file temporarily
    # temp_dir = r"C:\Users\ADMIN\Desktop\MYSP2"
    temp_dir = "audios"


    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio file
    audio_dir = os.path.join(script_dir, temp_dir)

    temp_path = os.path.join(audio_dir, file.filename)
    file.save(temp_path)
    # Redirect stdout to capture print statements
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        mysp.mysptotal(file.filename.split('.')[0], audio_dir)
        sys.stdout = sys.__stdout__  # Reset redirect.
        output = captured_output.getvalue()
        
        # Process the captured output to extract the data
        output_lines = output.strip().split('\n')
        data = {}
        for line in output_lines:
            if line.strip():  # Ignore empty lines
                parts = line.split(maxsplit=1)
                if len(parts) == 2:  # Only process lines that can be split into exactly two parts
                    key, value = parts
                    if key.strip() == 'number_':
                        key = 'number_of_syllables'
                        value = value.replace('of_syllables ', '')
                    data[key.strip()] = value.strip()

        # Remove the temporary file after processing

        # If empty response send assign score of 0 to all
        if num_words == 0 :
            content_score=0
            comments={}
            comments['Content']= ' Your response should not be empty.'

            content_score = 0.0
            pronounciation_score = 0.0
            fluency_score = 0.0
            response = jsonify({ 
                'content_score': content_score,
                'pronounciation_score': pronounciation_score,
                'fluency_score': fluency_score,
                'comment': comments}) 
        
            print("Finishing RA1 ----------------------------------------------------")        
            return response

        # OTHERWISE IF WORDS ARE MORE THAN 0
        else:
            # temp=summary.split('.')
            # summary=temp[0]
            script = script.replace('\n', '')
            if 'number_of_pauses' in data:
                pauses = data['number_of_pauses']
                duration = data['original_duration']
                speaking_dur = data['speaking_duration']   
                content_score, total_score, correctinds, incorrectinds, fluency_score, comments, pronounciation_remarks, pronounciation_score, correct_words_array = readaloudscoring(script, user_response, pauses, num_words, duration, speaking_dur, file)
                
                if content_score == 0:
                    fluency_score = 0
                    pronounciation_score = 0                    

                response = jsonify({ 
                    'content_score': content_score,
                    'total_content_score': total_score,
                    'matched_indices': correctinds,
                    'mismatched_indices': incorrectinds,
                    'comments': comments,
                    'pronounciation_remarks': pronounciation_remarks,
                    'pronounciation_score': pronounciation_score,
                    'fluency_score': fluency_score,
                    'correct_words': correct_words_array
                })
                print("Finishing RA2 ----------------------------------------------------")
                return response
            
            else:
                # Handle the case where 'number_of_pauses' is not present
                comments1 = 'The sound of the audio wasnt clear.'
                content_score, fluency_score, pronounciation_score, total_content_score = readaloudscoring1(script, user_response)
                print("Finishing RA3----------------------------------------------------")                
                return jsonify({
                    'content_score': content_score,
                    'fluency_score': fluency_score,
                    'pronunciation_score': pronounciation_score,
                    'total_content_score': total_content_score,
                    'comments': comments1
                })
    
    except Exception as e:
        sys.stdout = sys.__stdout__  # Reset redirect on exception.
        # logging.error(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    


@application.route('/answershortquestions', methods=['POST'])
def answershortquestions():
    data = request.json
    question = data['question']
    user_answer = data['user_answer']
    answer_list = data['answer_list']

    words = user_answer.split()  # Splits the user answer into individual words
    print("Words::", words)
    num_words = len(words)  # Gets the total count of words
    print("Number of words:", num_words)

    # If empty response send assign score of 0 to all
    if num_words == 0 :
        comments={}
        comments['Content']= ' Your response should not be empty.'

        content_score = 0.0
        response = jsonify({ 
            'content_score': content_score,
            'comment': comments}) 
    
        return response


    else:
        content_score = answershort(question, answer_list, user_answer)
        return jsonify({
            'content_score': content_score
        })


@application.route('/essay', methods=['POST'])
def essay_endpoint():
    try:
        data = request.json
        essay = data['essay']
        question = data['question']
        # Check if the length of the essay is between 200 and 300 words
        major_aspect, minor_aspect = data['major_aspect'],data['minor_aspect']
        print("Major aspects: ", major_aspect)
        print("minor aspects: ",minor_aspect)
        
        
        # sentences,accent,index=check_accent(essay)
        accent1= identify_accent(essay)
        print("accent: ",accent1)
        content_score, grammar_score, vocab_range_score, spelling_score, form_score, general_linguistic_range_score, development_structure_coherence_score,total_score,correct_words,comments, grammar_mistakes, misspelled_indices, grammtical_indices = score_essay(essay, question,major_aspect,minor_aspect,accent1)
        # if sentences!='1':
        #     diff_score=compare_accents(sentences,accent,index)
        # else:
        #     diff_score=0

        # if diff_score != 0:
        #     print("Different accent detected")
        #     print("No of different accent sentences: ",diff_score)
        #     grammar_score,spelling_score,development_structure_coherence_score= calculate_deductions(diff_score,grammar_score,spelling_score,development_structure_coherence_score)
        temp_mistakes =  get_response_from_openai(essay)

        mistakes = []  
        mistakes_list = [] 
        spelling_mistakes_list = []

        # (max_score - each_mistake * total_mistakes)
        grammar_score = 0 if len(mistakes_list) > 4 else (2 - 0.5 * len(mistakes_list))

        print("correct words: ",correct_words)

        return jsonify({
        'total_score': total_score,
        'content_score': content_score,
        'grammar_score': grammar_score,
        'spelling_score': spelling_score,
        'form_score': form_score,
        'general_linguistic_range_score': general_linguistic_range_score,
        'development_structure_coherence_score': development_structure_coherence_score,
        'vocab_range_score': vocab_range_score,
        'corrected words': correct_words,
        'comments': comments,
        'accent': accent1,
        'grammar mistakes': grammar_mistakes,
        'misspelled Indices': misspelled_indices,
        'grammatical mistakes indices': grammtical_indices,
        "mistakes" : mistakes_list,
        "spelling_mistakes": spelling_mistakes_list,
        "temp_mistakes": temp_mistakes
    })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@application.route('/respondtosituation', methods=['POST'])
def respondtosituation():
    mysp = __import__("my-voice-analysis")
    print("Starting RTS ----------------------------------------------------")    
    # Ensure the 'audiofile' is in the request files
    if 'audiofile' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['audiofile']
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    # Fetch user_text from form-data
    user_text = request.form.get('user_text', '')

    # Fetch major_aspects and minor_aspects from form-data and parse them into lists
    major_aspects_str = request.form.get('major_aspects', '[]')
    minor_aspects_str = request.form.get('minor_aspects', '[]')

    try:
        major_aspects = json.loads(major_aspects_str)  # Use json.loads for JSON encoded strings
        minor_aspects = json.loads(minor_aspects_str)  # Use json.loads for JSON encoded strings
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid format for aspects"}), 400
    
    # Print statements for debugging
    print(f"Major Aspects:: {major_aspects}")
    print(f"Minor Aspects:: {minor_aspects}")
    print(f"User text:: {user_text}")

    # Check if required fields are present
    if not major_aspects or not minor_aspects or not user_text:
        print("Ending RTS1 ----------------------------------------------------")        
        return jsonify({
                'appropriacy_score': 0.0,
                'fluency_score': 0.0,
                'pronunciation_score': 0.0,
                'comment': 'Kindly provide the content to get a score.'
            })
  
        
    # Save the uploaded file temporarily
    # temp_dir = r"C:\Users\ADMIN\Desktop\MYSP2"
    temp_dir = "audios"


    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # print("SCRIPT::", script_dir)
    # Construct the full path to the directory containing the audio file
    audio_dir = os.path.join(script_dir, temp_dir)
    print("SCRIPT2222::", audio_dir)

    temp_path = os.path.join(audio_dir, file.filename)
    print("SCRIPT2222555::", temp_path)
    file.save(temp_path)
    # mysp.mysptotal(file.filename.split('.')[0], temp_dir)
    # print(temp_path)
    # print("T1::", file.filename.split('.')[0])
    # print("T2::", temp_dir)
    # Redirect stdout to capture print statements
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        mysp.mysptotal(file.filename.split('.')[0], audio_dir)
        sys.stdout = sys.__stdout__  # Reset redirect.
        output = captured_output.getvalue()
        
        # Process the captured output to extract the data
        output_lines = output.strip().split('\n')
        data = {}
        for line in output_lines:
            if line.strip():  # Ignore empty lines
                parts = line.split(maxsplit=1)
                if len(parts) == 2:  # Only process lines that can be split into exactly two parts
                    key, value = parts
                    if key.strip() == 'number_':
                        key = 'number_of_syllables'
                        value = value.replace('of_syllables ', '')
                    data[key.strip()] = value.strip()

        # Remove the temporary file after processing
        # os.remove(temp_path)
        print("DATA::", data)
        # content_score, fluency_score, pronounciation_score, correct_word_indices = repeatsentencescoring(correct_text, user_text)
        # Check if 'number_of_pauses' exists in the data dictionary
        if 'number_of_pauses' in data:
            pauses = data['number_of_pauses']
            duration = data['original_duration']
            speaking_dur = data['speaking_duration']
            apropriacy_score, fluency_score, pronounciation_remarks, comments, pronounciation_score = respondscoring(user_text, major_aspects, minor_aspects, pauses, duration, speaking_dur, file)
            print("Ending RTS2 ----------------------------------------------------")            
            return jsonify({
                'number_of_pauses': data['number_of_pauses'],
                'original_duration': data['original_duration'],
                'rate_of_speech': data['rate_of_speech'],
                'speaking_duration': data['speaking_duration'],
                'appropriacy_score': apropriacy_score,
                'fluency_score': fluency_score,
                'pronounciation_remarks': pronounciation_remarks,
                'pronounciation_score': pronounciation_score,
                'comments': comments
            })
        else:
            # Handle the case where 'number_of_pauses' is not present
            comments1 = 'The sound of the audio wasnt clear.'
            apropriacy_score, fluency_score, pronounciation_score, comments = respondscoring1(user_text, major_aspects, minor_aspects)
            comments.append(comments1)
            print("Ending RTS2 ----------------------------------------------------")            
            return jsonify({
                'appropriacy_score': apropriacy_score,
                'fluency_score': fluency_score,
                'pronunciation_score': pronounciation_score,
                'comments': comments
            })

    except Exception as e:
        sys.stdout = sys.__stdout__  # Reset redirect on exception.
        # logging.error(f"An error occurred: {e}")
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        sys.stdout = sys.__stdout__



if __name__ == '__main__':
    application.run(debug=True)
