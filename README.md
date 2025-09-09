 # Chatbot-kubernetes

## Project Overview
This project implements a chatbot designed to interact with a Kubernetes cluster. It leverages Natural Language Processing (NLP) to understand user queries related to Kubernetes operations and executes corresponding commands. The chatbot aims to simplify Kubernetes management for users by providing an intuitive conversational interface.

## Features
- **Natural Language Understanding (NLU)**: Processes and understands user commands in natural language.
- **Kubernetes Integration**: Executes `kubectl` commands directly on a configured Kubernetes cluster.
- **RAG (Retrieval Augmented Generation)**: Utilizes a RAG system for enhanced context and accurate responses.
- **Session Management**: Maintains user session context for a more fluid conversational experience.
- **Authentication**: Includes an authentication module for secure access.
- **Logging**: Detailed logging of chatbot interactions and system events.

## Setup

### Prerequisites
- Python 3.8+
- Docker (for building the container image)
- Kubernetes cluster (Minikube, Docker Desktop Kubernetes, or a cloud-based cluster like GKE, EKS, AKS)
- `kubectl` configured to connect to your Kubernetes cluster.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/Chatbot-kubernetes.git
    cd Chatbot-kubernetes
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download spaCy model:**
    ```bash
    python3 -m spacy download en_core_web_sm
    ```

### Configuration

1.  **Kubernetes Context:** Ensure your `kubectl` is configured to the desired Kubernetes cluster. You can check your current context with:
    ```bash
    kubectl config current-context
    ```

2.  **Environment Variables:**
    The chatbot might require certain environment variables for configuration (e.g., API keys, database paths). Please refer to the application code (e.g., `app/server.py`, `app/config.py` if present) for specific requirements.

## Usage

### Running the Chatbot

1.  **Start the Flask server:**
    ```bash
    python app/server.py
    ```

2.  **Access the Chatbot:** Open your web browser and navigate to `http://127.0.0.1:5000` (or the address where the Flask app is running).

### Interacting with the Chatbot
Type your Kubernetes-related queries into the chat interface. Examples:
- "List all pods in the 'default' namespace."
- "Show me deployments."
- "Get logs for pod 'my-app-xyz'."

## Project Structure

```
Chatbot-kubernetes/
├── app/
│   ├── __pycache__/             # Python cache files
│   ├── auth.py                  # Authentication module
│   ├── bot.py                   # Core chatbot logic
│   ├── chroma_db/               # ChromaDB persistent storage
│   │   ├── ...                  # ChromaDB specific files
│   │   └── chroma.sqlite3
│   ├── clusters.py              # Kubernetes cluster interaction utilities
│   ├── debug_k8s.py             # Script for debugging Kubernetes interactions
│   ├── deletecl.sh              # Shell script for cluster deletion (example)
│   ├── docs/                    # Documentation and reference materials
│   │   ├── k8s_commands.txt
│   │   ├── k8s_deployments.txt
│   │   ├── k8s_pods.txt
│   │   └── procedures-internes.txt
│   ├── k8s_executor.py          # Executes Kubernetes commands
│   ├── k8s_executor2.py         # Alternative/updated Kubernetes executor
│   ├── logs/                    # Log files and session database
│   │   ├── chatbot.log
│   │   └── sessions.db
│   ├── mcp_context.py           # Context management for NLP
│   ├── nlp_parser.py            # Natural Language Processing parser
│   ├── nlp_parser2.py           # Alternative/updated NLP parser
│   ├── rag.py                   # Retrieval Augmented Generation module
│   ├── server.py                # Flask web server for the chatbot
│   ├── static/                  # Static web assets (CSS, JS, images)
│   │   ├── in.png
│   │   ├── script.js
│   │   ├── style.css
│   │   └── ubama.jpg
│   ├── templates/               # HTML templates for the web interface
│   │   └── index.html
│   └── venv/                    # Python virtual environment
├── Dockerfile                   # Dockerfile for containerization
├── requirements.txt             # Python dependencies
└── README.md                    # This README file
```


