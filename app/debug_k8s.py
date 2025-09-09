import os
import subprocess
import logging

# Setup basic logging to see the output clearly
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_diagnostic():
    """
    Isolates and diagnoses the kubectl execution problem.
    """
    print("--- STARTING KUBERNETES DIAGNOSTIC ---")

    # 1. Check the environment variable passed from the shell script
    kubeconfig_path = os.environ.get("CHATBOT_KUBECONFIG_PATH")
    if not kubeconfig_path:
        print("\n[FATAL] The CHATBOT_KUBECONFIG_PATH environment variable is NOT set.")
        print("--- DIAGNOSTIC FAILED ---")
        return

    print(f"\n[INFO] Script received kubeconfig path: {kubeconfig_path}")

    # 2. Verify the file at that path actually exists
    if not os.path.exists(kubeconfig_path):
        print(f"\n[FATAL] The file at the path '{kubeconfig_path}' does NOT exist.")
        print("--- DIAGNOSTIC FAILED ---")
        return

    print(f"\n[INFO] Verified file exists at: {kubeconfig_path}")

    # 3. Prepare the command and the specific environment for the subprocess
    command = ["kubectl", "get", "namespaces"]
    proc_env = os.environ.copy()
    proc_env["KUBECONFIG"] = kubeconfig_path

    print(f"\n[INFO] Attempting to run command: {' '.join(command)}")
    print(f"[INFO] Using KUBECONFIG: {proc_env['KUBECONFIG']}")

    # 4. Execute the command and capture all output
    try:
        result = subprocess.run(
            command,
            env=proc_env,
            capture_output=True,
            text=True,
            check=True, # This will raise an error if the command fails
            timeout=15
        )
        print("\n[SUCCESS] The command executed successfully!")
        print("\n--- STDOUT (Output) ---")
        print(result.stdout)
        print("--------------------")

    except subprocess.CalledProcessError as e:
        print("\n[FAILED] The command failed to execute. This is the root cause.")
        print("\n--- RAW STDERR (The Real Error Message) ---")
        print(e.stderr)
        print("---------------------------------------------")
        print("\n--- RAW STDOUT (If any) ---")
        print(e.stdout)
        print("-----------------------------")

    except Exception as e:
        print(f"\n[FAILED] An unexpected Python error occurred: {type(e).__name__}")
        print(f"\n--- EXCEPTION DETAILS ---")
        print(str(e))
        print("-------------------------")

    print("\n--- DIAGNOSTIC COMPLETE ---")


if __name__ == "__main__":
    run_diagnostic()
