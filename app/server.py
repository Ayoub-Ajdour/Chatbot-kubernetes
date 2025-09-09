# app/server.py
import warnings
warnings.filterwarnings("ignore")

from flask import Flask, request, jsonify, render_template, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import json

from bot import process_user_query_with_llm
from k8s_executor import execute_command
from mcp_context import update_context, get_context, get_history, update_history
from auth import require_auth, generate_token
from clusters import cluster_manager

app = Flask(__name__)

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'chatbot.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["300 per day", "100 per hour"]
)

def store_pending_command(session_id, command, cluster, query):
    context = get_context(session_id)
    if not isinstance(context, dict): context = {}
    context['pending_command'] = {"command": command, "cluster": cluster, "original_query": query}
    update_context(context, session_id)

def clear_pending_command(session_id):
    context = get_context(session_id)
    if isinstance(context, dict) and 'pending_command' in context:
        del context['pending_command']
    update_context(context, session_id)

@app.route('/')
def index():
    return render_template('index.html', clusters=cluster_manager.list_clusters())

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id: return jsonify({"error": "User ID required"}), 400
    token = generate_token(user_id)
    logging.info(f"User {user_id} logged in")
    return jsonify({"token": token})

@app.route('/chat', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth
def chat():
    data = request.get_json()
    user_input = data.get('message', '').strip()
    session_id = data.get('session_id', 'local-session')
    cluster = data.get('cluster', 'default')
    stream = data.get('stream', False)

    if not user_input:
        return jsonify({"response": "Please enter a message.", "action": "general"})

    conversation_history = get_history(session_id)
    query_with_context = f"{user_input} (on cluster: {cluster})"

    # D'abord, on appelle en mode non-stream pour voir si c'est une commande
    llm_response = process_user_query_with_llm(query_with_context, conversation_history, stream=False)
    response_type = llm_response.get("type")

    if response_type == "command":
        command = llm_response.get("command")
        explanation = llm_response.get("explanation")
        store_pending_command(session_id, command, cluster, user_input)
        response_text = (
            f"Suggested command: `{command}`\n"
            f"Explanation: {explanation}\n"
            f"(Cluster: {cluster})\n\n"
            "Do you want to execute this command?"
        )
        return jsonify({
            "response": response_text,
            "action": "pending_confirmation",
            "command": command,
            "cluster": cluster,
            "original_query": user_input
        })

    # Si ce n'est pas une commande et que le client veut un stream, on le fait.
    if stream:
        def stream_generator():
            full_response = []
            for chunk in process_user_query_with_llm(query_with_context, conversation_history, stream=True):
                full_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            final_answer = "".join(full_response)
            update_history(session_id, user_input, final_answer)
            logging.info(f"Stream finished for session {session_id}.")

        return Response(stream_generator(), mimetype='text/event-stream')
    
    # Sinon (client ne gérant pas le stream), on renvoie la réponse complète
    else:
        answer = llm_response.get("answer", "I'm sorry, I had trouble understanding that.")
        update_history(session_id, user_input, answer)
        return jsonify({"response": answer, "action": "general"})

@app.route('/regenerate', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth
def regenerate():
    data = request.get_json()
    original_query = data.get('original_query', '').strip()
    session_id = data.get('session_id', 'local-session')
    cluster = data.get('cluster', 'default')

    if not original_query: return jsonify({"error": "Original query is required."}), 400

    llm_response = process_user_query_with_llm(f"{original_query} (on cluster: {cluster})")

    if llm_response.get("type") == "command":
        command = llm_response.get("command")
        explanation = llm_response.get("explanation")
        store_pending_command(session_id, command, cluster, original_query)
        response_text = (
            f"Suggested command: `{command}`\n"
            f"Explanation: {explanation}\n"
            f"(Cluster: {cluster})\n\n"
            "Do you want to execute this command?"
        )
        return jsonify({
            "response": response_text,
            "action": "pending_confirmation",
            "command": command,
            "cluster": cluster,
            "original_query": original_query
        })
    else:
        return jsonify({"response": "I couldn't find another command for that request.", "action": "general"})


@app.route('/confirm', methods=['POST'])
@limiter.limit("20 per minute")
@require_auth
def confirm():
    data = request.get_json()
    session_id = data.get('session_id', 'local-session')
    user_confirmation = data.get('confirm', '').strip().lower()

    context = get_context(session_id)
    pending = context.get('pending_command') if isinstance(context, dict) else None
    if not pending: return jsonify({"response": "Error: No pending command found.", "action": "error"})

    command, cluster, user_query = pending['command'], pending['cluster'], pending['original_query']

    if user_confirmation == "yes":
        result = execute_command(command, cluster=cluster)
        clear_pending_command(session_id)
        update_history(session_id, user_query, f"Executed: `{command}`\nResult: {result}")
        return jsonify({"response": result, "action": "executed"})
    elif user_confirmation == "no":
        response_text = "Command not executed. What would you like to do next?"
        clear_pending_command(session_id)
        update_history(session_id, user_query, response_text)
        return jsonify({"response": response_text, "action": "cancelled"})
    else:
        return jsonify({"response": "Invalid input. Please respond with 'Yes' or 'No'.", "action": "error"})

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
