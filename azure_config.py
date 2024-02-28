# config.py

import json

with open("azure_config.json") as config_file:
    config_data = json.load(config_file)

AZURE_OPENAI_API_KEY = config_data.get("AZURE_OPENAI_API_KEY")