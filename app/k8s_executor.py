import subprocess
import shlex
import time
import logging
import os

from clusters import cluster_manager

def execute_command(command, cluster=None):
    """Execute a kubectl command using absolute paths."""
    logging.info(f"Preparing to execute command: '{command}' on cluster '{cluster or 'default'}'")

    # --- Read absolute paths from environment INSIDE the function for robustness ---
    KUBECTL_EXEC_PATH = os.environ.get("CHATBOT_KUBECTL_PATH")
    KUBE_CONFIG_FROM_ENV = os.environ.get("CHATBOT_KUBECONFIG_PATH")

    # --- Validate the paths inherited from the startup script ---
    if not KUBECTL_EXEC_PATH:
        logging.error("FATAL CONFIGURATION ERROR: CHATBOT_KUBECTL_PATH env var not set.")
        return "FATAL CONFIGURATION ERROR: The absolute path to kubectl was not provided."
    if not KUBE_CONFIG_FROM_ENV:
        logging.error("FATAL CONFIGURATION ERROR: CHATBOT_KUBECONFIG_PATH env var not set.")
        return "FATAL CONFIGURATION ERROR: The absolute path to kubeconfig was not provided."

    proc_env = os.environ.copy()
    proc_env["KUBECONFIG"] = KUBE_CONFIG_FROM_ENV

    if cluster:
        if not cluster_manager.set_cluster(cluster):
            return f"Error: Invalid cluster specified: {cluster}"

    if not command.startswith("kubectl "):
        return "Error: Only kubectl commands are allowed."

    try:
        # Replace 'kubectl' with the absolute path
        cmd_parts = shlex.split(command)
        cmd_parts[0] = KUBECTL_EXEC_PATH

        logging.info(f"Running subprocess with command: {cmd_parts}")
        result = subprocess.run(
            cmd_parts,
            env=proc_env,
            capture_output=True,
            text=True,
            check=True,
            timeout=20
        )
        # --- START OF UX IMPROVEMENT ---
        # If there is no output, provide a friendlier message.
        if result.stdout.strip():
            return result.stdout.strip()
        else:
            return "Command executed successfully. No resources found or no output was produced."
        # --- END OF UX IMPROVEMENT ---

    except FileNotFoundError:
        logging.error(f"FATAL: The system could not find the kubectl executable at '{KUBECTL_EXEC_PATH}'")
        return f"Error: The system could not find the kubectl executable. Path: {KUBECTL_EXEC_PATH}"
    except subprocess.CalledProcessError as e:
        # Return the stripped standard error for a cleaner UI display
        error_output = e.stderr.strip()
        logging.error(f"kubectl command failed. Stderr: {error_output}")
        return f"Error from server: {error_output}"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"
