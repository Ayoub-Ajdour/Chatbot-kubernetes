#!/bin/bash

# Exit on any error
set -e

# Navigate to project directory
cd ~/chatbot-k8s-v2

# --- START OF THE FINAL FIX: Find absolute paths for executables ---
# This is the only place these paths can be reliably found.
export CHATBOT_KUBECONFIG_PATH=$(realpath ~/.kube/config)
export CHATBOT_KUBECTL_PATH=$(which kubectl)

# Check that we found the files before starting anything.
if [ ! -f "$CHATBOT_KUBECONFIG_PATH" ]; then
    echo "FATAL ERROR: Kubernetes config file not found at $CHATBOT_KUBECONFIG_PATH"
    exit 1
fi
if ! [ -x "$CHATBOT_KUBECTL_PATH" ]; then
    echo "FATAL ERROR: 'kubectl' executable not found in your PATH."
    exit 1
fi

echo "Using Kubernetes config from: $CHATBOT_KUBECONFIG_PATH"
echo "Using kubectl executable at:  $CHATBOT_KUBECTL_PATH"
# --- END OF THE FINAL FIX ---

# Activate virtual environment
source venv/bin/activate

# Check for and kill old processes
echo "Checking for running services..."
if lsof -i :11434 > /dev/null; then kill -9 $(lsof -t -i :11434) || true; fi
if lsof -i :5000 > /dev/null; then kill -9 $(lsof -t -i :5000) || true; fi
sleep 1

# Start Ollama
echo "Starting Ollama server..."
ollama serve > ~/chatbot-k8s-v2/logs/ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 5

# Verify Ollama
if ! curl -s --fail http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama server failed to start. Check logs/ollama.log"
    exit 1
fi
echo "Ollama is running."

