import openai
import json
import datetime
import requests

def query_completion(prompt: str, engine: str = 'text-davinci-003', temperature: float = 0.5, max_tokens: int = 1500, top_p: int = 1, frequency_penalty: int = 0.5, presence_penalty: int = 0.2) -> object:
    """
    Function for querying GPT-3.
    """
    estimated_prompt_tokens = int(len(prompt.split()) * 1.6)
    estimated_answer_tokens = 2049 - estimated_prompt_tokens
    response = openai.Completion.create(
      engine=engine,
      prompt=prompt,
      temperature=temperature,
      max_tokens=min(4096-estimated_prompt_tokens, max_tokens),
      top_p=top_p,
      frequency_penalty=frequency_penalty,
      presence_penalty=presence_penalty
    )
    return response
    
def lambda_handler(event, context):
    openai.api_key = "REPLACE WITH YOUR OPENAI API KEY"
    
    print("Init:")
    print(datetime.datetime.now())
    print("Event:")
    print(event)

    table_data = "REPALCE WITH YOUR SQL TABLES STRING"
	pre_prompt = "Using only the below Postgresql tables, write a Postgresql query to "
    user_input = event['sessionState']['intent']['slots']['sql']['value']['originalValue']
    
    print("User input:")
    print(user_input)
    
    prompt = pre_prompt + user_input + table_data
        
    max_tokens = 1500
    
    response = query_completion(prompt)
    response_text = response['choices'][0]['text'].strip()
    
    print("OpenAI Response: ")
    print(response_text)
    
    database_query_url = 'REPLACE WITH YOUR WEB SERVER TO HANDLE SQL REQUESTS'
    database_response = requests.get(database_query_url, {"sql": response_text})
    #print("Database server response:")
    #print(database_response)
    database_data = database_response.json()
    
    print("Database data: ")
    print(database_data)
    
    final_response = "Here's the answer I found: " + database_data['formatted_response']
    final_response = final_response + "\n\nHere's the SQL query I used:\n\n" + response_text
    
    # The below prompts can be used to utilize GTP to format the data for us.
    # IMPORTANT: Be aware that you are sending real data over to GPT servers! Make sure it doesn't
    # contain anything sensitive or proprietary!
    #format_prompt = "Take the below JSON data and explain it in terms a human would understand.\n\n" + str(database_data)
    #format_prompt = "Take the below JSON data and format it as a plaintext table.\n\n" + str(database_data)
    #print("Format prompt:")
    #print(format_prompt)
    # Send the data to GPT for formatting
    #formatted_response = query_completion(format_prompt)
    #formatted_response_text = formatted_response['choices'][0]['text'].strip()
    # Debug the GPT response
    #print("OpenAI Formatted Response: ")
    #print(formatted_response_text)
    #final_response = formatted_response_text
    
    # This is a rough way to format smaller responses in python
    #response_list = []
    #for data in database_data:
    #    response_list.append(str(data))
    #final_response = "\n".join(response_list)
    
    response = {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": "openAiQuery",
                "state": "Fulfilled"
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": final_response
            }    
        ]
    }

    return response
