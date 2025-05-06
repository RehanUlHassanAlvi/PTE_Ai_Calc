
import json
from pprint import pprint

import boto3

list_mistakes_prompt = """
Task: I want you to analyze the given paragraph for grammar, punctuation, and spelling mistakes. 

Only list the mistakes in the below format and don't return the corrected paragraph:
#) Explain mistake and suggest solution in a single sentence (Mistake type).

Below are some paragraphs and the mistakes highlighted manually.

Paragraph #1): 
```
It well known that different people have different perceptual intellection *1 regarding the
aforementioned statement. In this essay, we will discuss whether negative impacts are important
or not; thus, it will lead to a plausible conclusion. As a further matter, those individuals who have
acclaimed themselves as a paradigm for alternative *3 have burnt the midnight oil for reaching
at desired *2 position.
```
Mistakes in Paragraph #1):
1) Intellections here (Pluralization error).
2) The between at desired (Grammar article error).
3) Should have an before it, or otherwise alternatives.
"""

def mistake_word_duplicated(mistake: dict):
    # return False
    pluralization_error_exists = False
    mistake_word = mistake.get("mistake_word", "").lower()
    mistake_explanation = mistake.get("mistake_explanation", "").lower() 

    if len(mistake_word) > 0 \
        and len(mistake_explanation) > 0:
        mistakes_explaination_words = mistake_explanation.split()
        count = mistakes_explaination_words.count(mistake_word)

        if count > 1:
            print(mistake_word)
            print(mistake_explanation)
            pluralization_error_exists = False

    return pluralization_error_exists

def sanitize_unescaped_quotes_and_load_json_str(s: str, strict=False) -> dict:
    js_str = s
    prev_pos = -1
    curr_pos = 0
    
    while curr_pos > prev_pos:
        prev_pos = curr_pos
        try:
            return json.loads(js_str, strict=strict)
        except json.JSONDecodeError as err:
            curr_pos = err.pos
            if curr_pos <= prev_pos:
                raise err
            
            # Find the previous " before err.pos
            prev_quote_index = js_str.rfind('"', 0, curr_pos)
            
            # Check if the quote found is part of a JSON key or value delimiter
            if prev_quote_index == 0 or js_str[prev_quote_index - 1] != '\\':
                # Escape it to \"
                js_str = js_str[:prev_quote_index] + "\\" + js_str[prev_quote_index:]
            else:
                # If the quote is already escaped, move forward without changing it
                continue


def filter_spelling_and_word_choice_mistakes(mistakes: dict):
    """
    Filter spelling and word choice mistakes from the given mistakes dictionary.
    
    return
        spelling_mistakes: list of spelling mistakes
        rem_word_choice_mistakes: filtered list mistakes after removing word choice mistakes
    """
    
    mistakes_list = mistakes.get("mistakes", [])

    # if None or "N/A" set in mistake.get("mistake_word")
    filtered_none_mistakes = []
    for mistake in mistakes_list:
        mistake_word = mistake.get("mistake_word")

        if mistake_word and \
            mistake_word != "N/A" and \
                len(mistake_word) <= 25:
            filtered_none_mistakes.append(mistake)
            
    # move spelling error in separate list, remove word choice errors 
    spelling_mistakes, rem_word_choice_mistakes = [], []

    for mistake in filtered_none_mistakes:
        mistake_explanation = mistake.get("mistake_explanation").lower()

        if "spelling" in mistake_explanation:
            spelling_mistakes.append(mistake)

        elif "word choice" in mistake_explanation \
            or "redundan" in mistake_explanation \
                or "comma splice" in mistake_explanation \
                    or "no mistake" in mistake_explanation \
                        or "Verb Choice error".lower() in mistake_explanation \
                            or "Incorrect word Usage".lower() in mistake_explanation \
                                or "unnecessary adverb".lower() in mistake_explanation: 
            continue

        # elif mistake_word_duplicated(mistake):
        #     continue

        else:
            rem_word_choice_mistakes.append(mistake)
    
    return spelling_mistakes, rem_word_choice_mistakes


def get_formatted_output_prompt(para) -> str:
    format_response_prompt_1 = f"""
Your task is to analyze the input paragraph and mistakes provided by the user. Format the response in the output json format provided below and only return json.

<input> 
{para}
</input>\n
"""
    format_response_prompt_2 = """
<output>
The JSON should follow this structure:
```
{
    "mistakes": [
        {
            "mistake_str": 'complete mistake sentence in the input paragraph for reference.,
            "mistake_explanation": 'Explain mistake and suggest solution in a single sentence (Mistake type).',
            "mistake_word": 'Mistake word/sequence'
        }
    ]
}
```
</output>
"""
    return format_response_prompt_1 + format_response_prompt_2


def generate_from_bedrock(
    prompt: str, query: str, model_name="anthropic.claude-3-haiku-20240307-v1:0", print_results=False
) -> str:
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime", region_name="us-east-1",
        aws_access_key_id='AKIAXYKJSDKSQCXYPALV', aws_secret_access_key='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'
    )

    user_message = {"role": "user", "content": query}
    messages = [user_message]

    # model params
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": prompt,
            "messages": messages,
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 100
        }
    )

    print("\n-- Bedrock Generating...")
    
    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=model_name,
        accept="application/json",
        contentType="application/json",
    )

    print(
        f"-- Token used by Bedrock model {model_name}: ",
        response.get("ResponseMetadata")
        .get("HTTPHeaders")
        .get("x-amzn-bedrock-input-token-count"),
    )

    resp_str = response.get("body").read().decode("utf-8")
    # print(resp_str, type(resp_str))

    response_body = json.loads(resp_str)

    result = response_body.get("content")[0].get("text")
    

    if print_results:
        print("--", result)

    return result

def get_response_from_claude(text: str, model_name : str='anthropic.claude-3-haiku-20240307-v1:0') -> dict:
    """
    Claude finds the mistakes in the paragraph and returns the response in a json format.
 
    result_dict: dict
        mistakes: list of mistakes
        spelling_mistakes: list of spelling mistakes
    """
    # out = str | mistakes in para listed.
    mistakes_list = generate_from_bedrock(
        prompt=list_mistakes_prompt, 
        query=text,
    )
    # print(mistakes_list)

    formatted_output_prompt = get_formatted_output_prompt(text)

    # out = json string | formatted response 
    formatted_mistakes_str = generate_from_bedrock(
        prompt=formatted_output_prompt,
        query=mistakes_list,
        model_name=model_name,
        # print_results=True
    )
    # print(formatted_mistakes)

    formatted_mistakes = f'''
    {formatted_mistakes_str}
    '''

    # formatted_mistakes = escape_json_string(formatted_mistakes_str)

    try:
        result_dict = json.loads(formatted_mistakes)
        print(f"- Generated response: {type(result_dict)}")

        print(f"- Original mistakes len: {len(result_dict['mistakes'])}")
        result_dict['spelling_mistakes'], result_dict['mistakes'] = filter_spelling_and_word_choice_mistakes(result_dict)
        print(f"- Mistakes len after filteration: {len(result_dict['mistakes'])}", "\n")
        # for mis in result_dict['mistakes']:
        #     pprint(mis)

        return result_dict
    
    except json.JSONDecodeError as e:
        print("The response could not be parsed as JSON.")
        try:
            result_dict = sanitize_unescaped_quotes_and_load_json_str(formatted_mistakes)
            print(f"- Generated response: {type(result_dict)}")

            print(f"- Original mistakes len: {len(result_dict['mistakes'])}")
            result_dict['spelling_mistakes'], result_dict['mistakes'] = filter_spelling_and_word_choice_mistakes(result_dict)
            print(f"- Mistakes len after filteration: {len(result_dict['mistakes'])}", "\n")

            return result_dict
        except Exception as e:
            print("The response couldn't be parsed, Got: ", e)
    
            raise Exception("The response couldn't be parsed, Got: ", e)
    
    except Exception as e:
        print("An error occurred while parsing the response:", e)
        raise Exception("An error in get_response_from_claude(): ", e)
    
    