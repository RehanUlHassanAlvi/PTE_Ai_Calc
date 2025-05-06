import json
import time
from openai import OpenAI 
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_response_from_openai(text: str, model_name: str = 'gpt-4o-mini') -> dict:
    prompt = """
    You are an Intelligent Assistant who analyses the text efficiently for grammatical mistakes only.
    """
    essay = f"""
    Please check the following text for grammatical mistakes only. Do not point out spelling mistakes. Do not suggest changes for word choice, style, misplaced modifiers, or phrasing. Only identify and correct strict grammatical errors without changing the content or meaning of the sentences. For each mistake, return the following details:
    - incorrect: The incorrect word or phrase
    - corrected: The corrected version
    - explanation: A brief explanation of the grammatical error
    - error_name: The name of the grammatical error
    - exact_mistake_word: The exact word considered a mistake
    - phrase_with_mistake: The phrase where the mistake appears
    - start_index: The exact starting index of the mistake word in the entire text
    - end_index: The exact ending index of the mistake word in the entire text
    If no grammatical mistakes are found, return an empty array. Return the response in JSON format.
    Ensure that the start_index and end_index reflect the position of the mistake word within the entire text.
    Text: {text}
    """
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # Increment attempt counter
            attempt += 1
            
            # Make API call
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": essay
                    }
                ]
            )
            
            # Try to parse the response as JSON
            result = json.loads(response.choices[0].message.content)
            
            # If JSON parsing is successful, return the result
            return result
        
        except json.JSONDecodeError:
            print(f"Attempt {attempt}: Failed to parse JSON. Retrying...")
            
            # Add a small delay between attempts to avoid rate limiting
            time.sleep(1)
        
        except Exception as e:
            print(f"Attempt {attempt}: An unexpected error occurred: {e}")
            
            # Add a small delay between attempts
            time.sleep(1)
    
    # If all attempts fail, raise an exception
    raise Exception("Failed to get a valid JSON response after 3 attempts")
