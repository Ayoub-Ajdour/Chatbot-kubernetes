import spacy
import logging
import re

# Load the SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("SpaCy model 'en_core_web_sm' loaded successfully.")
except IOError:
    logging.error("SpaCy model 'en_core_web_sm' not found. Run: 'python -m spacy download en_core_web_sm'")
    nlp = None

# --- Keywords for high-level intent detection (now including French) ---
COMMAND_INDICATORS = [
    # English Verbs
    "get", "describe", "logs", "delete", "apply", "create", "exec", "run", "top", "explain", "show", "list", "remove",
    # French Verbs
    "affiche", "décris", "supprime", "crée", "exécute", "liste", "montre",
    # Common Resources (English & French)
    "pods", "pod", "po", "p",
    "deployments", "deployment", "deploy", "d",
    "services", "service", "svc",
    "namespaces", "namespace", "ns", "espaces de noms",
    "nodes", "node", "no", "noeuds",
    "configmaps", "configmap", "cm",
    "secrets", "secret",
    "ingresses", "ingress", "ing"
]

CLUSTER_INDICATORS = ["on cluster", "in cluster", "for cluster", "cluster", "on", "sur le cluster", "dans le cluster"]

def _extract_cluster(text):
    """
    Finds a cluster name, extracts its value, and returns the value.
    """
    for indicator in CLUSTER_INDICATORS:
        pattern = re.compile(rf'\b{re.escape(indicator)}\s+([a-zA-Z0-9_-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            cluster_value = match.group(1)
            logging.info(f"Extractor found cluster '{cluster_value}' via indicator '{indicator}'.")
            return cluster_value
    return None

def detect_intent(user_input):
    """
    Detects if the user input is likely a command, a general query,
    or a simple greeting. This is a high-level classification.
    """
    logging.info(f"Starting high-level intent detection for: '{user_input}'")
    if not nlp:
        return {"action": "general", "query": user_input, "error": "SpaCy model not loaded."}

    # Normalize text to lower case for keyword matching
    lower_input = user_input.lower()
    
    # Check if the input contains any of the command-related keywords
    if any(indicator in lower_input for indicator in COMMAND_INDICATORS):
        logging.info("Detected potential k8s command. Routing for command generation.")
        
        # We still extract the cluster here to pass it along
        cluster = _extract_cluster(user_input)
        
        return {
            "action": "k8s_command_generation_needed",
            "query": user_input,
            "cluster": cluster or "default"
        }

    # If no command keywords are found, treat it as a general query for the RAG system
    logging.info("No command indicators found. Treating as general query.")
    return {"action": "general", "query": user_input}
