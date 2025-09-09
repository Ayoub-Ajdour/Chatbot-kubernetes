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

# Keywords for command detection
K8S_COMMAND_VERBS = ["get", "describe", "logs", "delete", "apply", "create", "exec", "run", "top", "explain"]

# --- START OF THE PERFECTION FIX ---
# The resource list is now expanded with all common singular and plural forms.
# This makes the command detection much more robust and "perfect".
K8S_RESOURCES = [
    # Workloads
    "pods", "pod", "po", 
    "deployments", "deployment", "deploy",
    "statefulsets", "statefulset", "sts",
    "daemonsets", "daemonset", "ds",
    "jobs", "job",
    "cronjobs", "cronjob", "cj",
    
    # Networking
    "services", "service", "svc",
    "ingresses", "ingress", "ing",
    
    # Configuration
    "configmaps", "configmap", "cm",
    "secrets", "secret",
    
    # Storage
    "persistentvolumes", "persistentvolume", "pv",
    "persistentvolumeclaims", "persistentvolumeclaim", "pvc",
    "storageclasses", "storageclass", "sc",
    
    # Cluster
    "nodes", "node", "no",
    "namespaces", "namespace", "ns"
]
# --- END OF THE PERFECTION FIX ---

NAMESPACE_INDICATORS = ["in namespace", "from namespace", "namespace", "-n", "in", "from"]
CLUSTER_INDICATORS = ["on cluster", "in cluster", "for cluster", "cluster", "on"]


def _extract_parameter_and_clean(text, indicators):
    """
    Finds a parameter based on a list of indicators, extracts its value,
    and returns the value along with the text cleaned of the indicator phrase.
    It sorts indicators by length to prioritize more specific matches.
    """
    sorted_indicators = sorted(indicators, key=len, reverse=True)
    
    for indicator in sorted_indicators:
        pattern = re.compile(rf'\b{re.escape(indicator)}\s+([a-zA-Z0-9_-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        
        if match:
            param_value = match.group(1)
            cleaned_text = text[:match.start()] + text[match.end():]
            logging.info(f"Extractor found param '{param_value}' via indicator '{indicator}'. Cleaned text: '{cleaned_text.strip()}'")
            return param_value, cleaned_text.strip()
            
    return None, text


def detect_intent(user_input, command_context=""):
    """
    A more robust and accurate intent detector for Kubernetes commands.
    """
    logging.info(f"Starting intent detection for: '{user_input}'")
    if not nlp:
        return {"action": "general", "query": user_input, "error": "SpaCy model not loaded."}

    work_text = user_input
    
    cluster, work_text = _extract_parameter_and_clean(work_text, CLUSTER_INDICATORS)
    namespace, work_text = _extract_parameter_and_clean(work_text, NAMESPACE_INDICATORS)

    tokens = work_text.lower().split()
    verb = next((token for token in tokens if token in K8S_COMMAND_VERBS), None)
    resource = next((token for token in tokens if token in K8S_RESOURCES), None)

    if verb and resource:
        base_command = f"kubectl {work_text}"
        final_command = base_command
        
        if namespace:
            final_command += f" -n {namespace}"

        final_command = re.sub(r'\s+', ' ', final_command).strip()
        logging.info(f"Detected k8s_command. Final Command: '{final_command}', Target Cluster: '{cluster or 'default'}'")
        
        return {
            "action": "k8s_command",
            "command": final_command,
            "cluster": cluster or "default"
        }

    logging.info("No clear k8s command signature found. Treating as general query.")
    return {"action": "general", "query": user_input}import spacy
import logging
import re

# Load the SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logging.info("SpaCy model 'en_core_web_sm' loaded successfully.")
except IOError:
    logging.error("SpaCy model 'en_core_web_sm' not found. Run: 'python -m spacy download en_core_web_sm'")
    nlp = None

# Keywords for command detection
K8S_COMMAND_VERBS = ["get", "describe", "logs", "delete", "apply", "create", "exec", "run", "top", "explain"]

# --- START OF THE PERFECTION FIX ---
# The resource list is now expanded with all common singular and plural forms.
# This makes the command detection much more robust and "perfect".
K8S_RESOURCES = [
    # Workloads
    "pods", "pod", "po", 
    "deployments", "deployment", "deploy",
    "statefulsets", "statefulset", "sts",
    "daemonsets", "daemonset", "ds",
    "jobs", "job",
    "cronjobs", "cronjob", "cj",
    
    # Networking
    "services", "service", "svc",
    "ingresses", "ingress", "ing",
    
    # Configuration
    "configmaps", "configmap", "cm",
    "secrets", "secret",
    
    # Storage
    "persistentvolumes", "persistentvolume", "pv",
    "persistentvolumeclaims", "persistentvolumeclaim", "pvc",
    "storageclasses", "storageclass", "sc",
    
    # Cluster
    "nodes", "node", "no",
    "namespaces", "namespace", "ns"
]
# --- END OF THE PERFECTION FIX ---

NAMESPACE_INDICATORS = ["in namespace", "from namespace", "namespace", "-n", "in", "from"]
CLUSTER_INDICATORS = ["on cluster", "in cluster", "for cluster", "cluster", "on"]


def _extract_parameter_and_clean(text, indicators):
    """
    Finds a parameter based on a list of indicators, extracts its value,
    and returns the value along with the text cleaned of the indicator phrase.
    It sorts indicators by length to prioritize more specific matches.
    """
    sorted_indicators = sorted(indicators, key=len, reverse=True)
    
    for indicator in sorted_indicators:
        pattern = re.compile(rf'\b{re.escape(indicator)}\s+([a-zA-Z0-9_-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        
        if match:
            param_value = match.group(1)
            cleaned_text = text[:match.start()] + text[match.end():]
            logging.info(f"Extractor found param '{param_value}' via indicator '{indicator}'. Cleaned text: '{cleaned_text.strip()}'")
            return param_value, cleaned_text.strip()
            
    return None, text


def detect_intent(user_input, command_context=""):
    """
    A more robust and accurate intent detector for Kubernetes commands.
    """
    logging.info(f"Starting intent detection for: '{user_input}'")
    if not nlp:
        return {"action": "general", "query": user_input, "error": "SpaCy model not loaded."}

    work_text = user_input
    
    cluster, work_text = _extract_parameter_and_clean(work_text, CLUSTER_INDICATORS)
    namespace, work_text = _extract_parameter_and_clean(work_text, NAMESPACE_INDICATORS)

    tokens = work_text.lower().split()
    verb = next((token for token in tokens if token in K8S_COMMAND_VERBS), None)
    resource = next((token for token in tokens if token in K8S_RESOURCES), None)

    if verb and resource:
        base_command = f"kubectl {work_text}"
        final_command = base_command
        
        if namespace:
            final_command += f" -n {namespace}"

        final_command = re.sub(r'\s+', ' ', final_command).strip()
        logging.info(f"Detected k8s_command. Final Command: '{final_command}', Target Cluster: '{cluster or 'default'}'")
        
        return {
            "action": "k8s_command",
            "command": final_command,
            "cluster": cluster or "default"
        }

    logging.info("No clear k8s command signature found. Treating as general query.")
    return {"action": "general", "query": user_input}
