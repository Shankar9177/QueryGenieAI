# Include your utility functions that are reused across the application
from pandasai.smart_dataframe import SmartDataframe
import pandas as pd

def update_chat(messages, role, content):
    """
    Updates messages with the new message content from the user or the assistant.
    """
    messages.append({"role": role, "content": content})
    return messages

def get_dataframe_from_response(response):
    """
    Extracts a DataFrame from a pandasai response.
    """
    if isinstance(response, SmartDataframe):
        # Convert SmartDataframe to pandas DataFrame
        df_result = response._df
    elif type(response) in (pd.core.frame.DataFrame, pd.DataFrame):
        df_result = response
    else:
        df_result = None
    return df_result
import openai

def get_initial_message():
    messages=[
            {"role": "system", "content": "You are a helpful AI Tutor. Who anwers brief questions about AI."},
            {"role": "user", "content": "I want to learn AI"},
            {"role": "assistant", "content": "Thats awesome, what do you want to know aboout AI"}
        ]
    return messages

def get_chatgpt_response(messages, model="gpt-3.5-turbo"):
    print("model: ", model)
    response = openai.ChatCompletion.create(
    model=model,
    messages=messages
    )
    return  response['choices'][0]['message']['content']

def update_chat(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages
