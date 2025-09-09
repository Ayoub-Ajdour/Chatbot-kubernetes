# app/bot.py

import requests
import json
import logging
import os
import re
# Importe la fonction de récupération de contexte depuis rag.py
from rag import retrieve_context

def process_user_query_with_llm(user_query, conversation_history="", stream=False):
    """
    Utilise le LLM pour traiter la requête de l'utilisateur.
    Gère à la fois les réponses structurées (JSON) et les réponses en streaming.
    """
    logging.info(f"Processing query with new LLM brain: '{user_query}'")

    # Étape 1: Récupérer le contexte pertinent depuis la base de données vectorielle (RAG)
    relevant_docs_context = retrieve_context(user_query)
    logging.info(f"Retrieved RAG context: {relevant_docs_context}")
    
    # Si le client demande un streaming, on utilise un prompt plus simple pour une réponse directe.
    if stream:
        stream_prompt = (
            "You are a helpful Kubernetes assistant. Based on the following context and conversation history, "
            "answer the user's question directly and conversationally.\n"
            f"Context: {relevant_docs_context}\n"
            f"History: {conversation_history}\n"
            f"User Question: {user_query}\n\n"
            "Answer:"
        )
        # Retourne un générateur pour le streaming
        return _query_ollama_stream(stream_prompt)

    # Sinon, on utilise le prompt complexe pour obtenir un JSON structuré (commande ou question).
    prompt = (
        "You are an expert Kubernetes assistant that can understand English and French. "
        "Your goal is to analyze the user's request, the conversation history, and the provided context, then respond in a specific JSON format. "
        "There are two possible response types: 'question' or 'command'.\n\n"
        "1. If the user is asking a general question (e.g., 'what is a pod?', 'how do I scale a deployment?'):\n"
        "   - First, check the 'RETRIEVED CONTEXT' section. If it contains relevant information, use it to build your answer.\n"
        "   - If the context is not relevant, use your general knowledge.\n"
        "   - Your JSON response must be: {\"type\": \"question\", \"answer\": \"<Your clear and helpful answer here>\"}\n\n"
        "2. If the user is asking for a kubectl command (e.g., 'show me the pods', 'create a namespace called test'):\n"
        "   - You must generate the simplest, most common, and directly executable `kubectl` command.\n"
        "   - Provide a very brief, one-sentence explanation of what the command does.\n"
        "   - Your JSON response must be: {\"type\": \"command\", \"command\": \"<The kubectl command>\", \"explanation\": \"<The brief explanation>\"}\n\n"
        "--- RETRIEVED CONTEXT ---\n"
        f"{relevant_docs_context}\n"
        "--- END CONTEXT ---\n\n"
        "--- CONVERSATION HISTORY ---\n"
        f"{conversation_history}\n"
        "--- END HISTORY ---\n\n"
        f"User's Latest Request: \"{user_query}\"\n\n"
        "Respond with only the JSON object, and nothing else."
    )

    logging.info("Sending master prompt for JSON response to LLM.")
    try:
        response_text = _query_ollama(prompt)
        clean_json_string = re.sub(r'```json\s*|\s*```', '', response_text).strip()
        logging.info(f"LLM Raw Response: {response_text}")
        logging.info(f"Cleaned JSON string: {clean_json_string}")
        json_response = json.loads(clean_json_string)
        if 'type' not in json_response or ('answer' not in json_response and 'command' not in json_response):
            raise ValueError("LLM response is missing required keys.")
        return json_response
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from LLM response. String was: '{clean_json_string}'. Error: {e}")
        return {"type": "question", "answer": "Sorry, I received an unexpected response from my AI brain. Please try rephrasing your request."}
    except Exception as e:
        logging.error(f"An unexpected error occurred in process_user_query_with_llm: {e}")
        return {"type": "question", "answer": f"An unexpected error occurred: {e}"}

def _query_ollama(prompt):
    """Fonction interne pour envoyer un prompt à Ollama et obtenir une réponse complète (non-stream)."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral:instruct", "prompt": prompt, "stream": False, "options": {"temperature": 0.1}}
        )
        response.raise_for_status()
        full_response_data = response.json()
        return full_response_data.get("response", "")
    except requests.RequestException as e:
        logging.error(f"Error connecting to Ollama: {str(e)}")
        return "{\"type\": \"question\", \"answer\": \"Error: Could not connect to the language model.\"}"

def _query_ollama_stream(prompt):
    """Fonction interne pour envoyer un prompt à Ollama et streamer la réponse."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral:instruct", "prompt": prompt, "stream": True, "options": {"temperature": 0.1}},
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_lines():
            if chunk:
                decoded_chunk = json.loads(chunk)
                yield decoded_chunk.get("response", "")
    except requests.RequestException as e:
        logging.error(f"Error connecting to Ollama for streaming: {str(e)}")
        yield "Error: Could not connect to the language model."
