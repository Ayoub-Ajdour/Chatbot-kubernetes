import subprocess
import shlex
import time
import logging
import os

from clusters import cluster_manager

# --- START OF THE FINAL FIX: Read absolute paths from environment ---
KUBE_CONFIG_FROM_ENV = os.environ.get("CHATBOT_KUBECONFIG_PATH")
KUBECTL_EXEC_PATH = os.environ.get("CHATBOT_KUBECTL_PATH")
# --- END OF THE FINAL FIX ---

def execute_command(command, cluster=None):
    """Execute a kubectl command using absolute paths."""
    logging.info(f"Preparing command: {command}, cluster: {cluster}")

    # --- START OF THE FINAL FIX: Validate the paths before execution ---
    if not KUBECTL_EXEC_PATH:
        return "FATAL CONFIGURATION ERROR: The absolute path to kubectl was not provided."
    if not KUBE_CONFIG_FROM_ENV:
        return "FATAL CONFIGURATION ERROR: The absolute path to kubeconfig was not provided."
    # --- END OF THE FINAL FIX ---

    proc_env = os.environ.copy()
    proc_env["KUBECONFIG"] = KUBE_CONFIG_FROM_ENV

    if cluster:
        if not cluster_manager.set_cluster(cluster):
            return f"Error: Invalid cluster specified: {cluster}"

    if not command.startswith("kubectl "):
        return "Error: Only kubectl commands are allowed."

    try:
        # Split the command string, e.g., "kubectl get pods" -> ["kubectl", "get", "pods"]
        cmd_parts = shlex.split(command)

        # Replace "kubectl" with the absolute path, e.g., "/usr/local/bin/kubectl"
        cmd_parts[0] = KUBECTL_EXEC_PATH

        logging.info(f"Running subprocess with absolute path: {cmd_parts}")

        result = subprocess.run(
            cmd_parts, # Use the list with the absolute path
            env=proc_env,
            capture_output=True,
            text=True,
            check=True,
            timeout=20
        )
        return result.stdout.strip()
    except FileNotFoundError:
        # This error happens if the executable path is wrong.
        logging.error(f"FATAL: Could not find the kubectl executable at '{KUBECTL_EXEC_PATH}'")
        return f"Error: The system could not find the kubectl executable. Path: {KUBECTL_EXEC_PATH}"
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip()
        logging.error(f"kubectl command failed. Stderr: {error_output}")
        return f"Error from server: {error_output}"
    except Exception as e:
        logging.error(f"An unexpected error occurred in execute_command: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"
