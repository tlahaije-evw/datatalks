from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Laad de .env file
load_dotenv()

def api_call(message, prompt, model='gpt-4o'):
    """
    Maakt een API-oproep naar de OpenAI Azure-service met een specifiek prompt en bericht.
    
    Parameters:
        message (str): De tekst die de gebruiker naar de API stuurt.
        prompt (str): De specifieke prompt die de API moet volgen.
        model (str): De naam van de Azure-deployment (bijv. 'gpt-4o').

    Returns:
        str: Het antwoord van de API.
    """
    # Haal de API-sleutel en URL uit de omgevingsvariabelen
    api_key = os.getenv('API_KEY_AI')
    base_url = os.getenv('API_URL_AI')  # Basis-URL zonder pad
    deployment_name = model  # Specifieke naam van de deployment
    api_version = "2024-08-01-preview"  # Versie van de Azure API

    print(base_url)

    # Message met de prompt als parameter
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": str(message)}
    ]

    # Initialiseer de AzureOpenAI client
    client = AzureOpenAI(
        azure_endpoint=base_url,  # Alleen de basis-URL
        api_key=api_key,
        api_version=api_version
    )

    # API call: stuurt de boodschap naar het model
    response = client.chat.completions.create(
        model=model,  # Gebruik de deployment-naam hier
        messages=messages
    )

    # Extracteer de inhoud van het antwoord
    response_message = response.choices[0].message.content

    return response_message