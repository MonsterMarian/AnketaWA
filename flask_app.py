import os
import json
from flask import Flask, render_template, request, jsonify
from config import RESET_TOKEN, VOTE_FILE, QUESTIONS
from datetime import datetime
from filelock import FileLock

VOTERS_FILE = "data/voters.txt"
META_FILE = "data/meta.json"

app = Flask(__name__)

# Ensure data directory exists
os.makedirs(os.path.dirname(VOTE_FILE), exist_ok=True)

# File locks for thread/process safety
meta_lock = FileLock("data/meta.json.lock")
vote_lock = FileLock("data/votes.json.lock")
voters_lock = FileLock("data/voters.txt.lock")

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

def load_votes():
    with vote_lock:
        if not os.path.exists(VOTE_FILE):
            votes = {opt["id"]: 0 for opt in QUESTIONS["options"]}
            with open(VOTE_FILE, 'w', encoding='utf-8') as f:
                json.dump(votes, f, indent=4)
            return votes
        with open(VOTE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def load_meta():
    with meta_lock:
        if not os.path.exists(META_FILE):
            meta = {"last_vote": "Nikdy", "total_clicks": 0}
            with open(META_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=4)
            return meta
        with open(META_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_meta(meta):
    with meta_lock:
        with open(META_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=4)

def save_votes(votes):
    with vote_lock:
        with open(VOTE_FILE, 'w', encoding='utf-8') as f:
            json.dump(votes, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html', quest=QUESTIONS)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/results', methods=['GET'])
def get_results():
    votes = load_votes()
    return jsonify(votes)

@app.route('/api/vote', methods=['POST'])
def vote():
    # 1. Check Cookie
    if request.cookies.get('voted'):
        return jsonify({"error": "You have already voted (cookie)"}), 403

    # 2. Check IP Address safely
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    with voters_lock:
        if os.path.exists(VOTERS_FILE):
            with open(VOTERS_FILE, 'r') as f:
                voters = f.read().splitlines()
                if user_ip in voters:
                    return jsonify({"error": "You have already voted (IP)"}), 403

    data = request.get_json()
    option_id = data.get('option')
    
    valid_ids = [opt["id"] for opt in QUESTIONS["options"]]
    if option_id not in valid_ids:
        return jsonify({"error": "Invalid option"}), 400
    
    # Save Vote
    votes = load_votes()
    votes[option_id] += 1
    save_votes(votes)
    
    # Update Meta
    meta = load_meta()
    meta["last_vote"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    meta["total_clicks"] += 1
    save_meta(meta)

    # Log IP
    with voters_lock:
        with open(VOTERS_FILE, 'a') as f:
            f.write(f"{user_ip}\n")
    
    response = jsonify(votes)
    response.set_cookie('voted', 'true', max_age=60*60*24*30) # 30 days
    return response

@app.route('/api/reset', methods=['POST'])
def reset():
    token = request.headers.get('Authorization', '').strip()
    if token != RESET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Reset votes
    votes = {opt["id"]: 0 for opt in QUESTIONS["options"]}
    save_votes(votes)
    
    # Reset meta
    save_meta({"last_vote": "Nikdy", "total_clicks": 0})

    # Clear IP log
    with voters_lock:
        if os.path.exists(VOTERS_FILE):
            # Write empty string to avoid removing an open file on Windows
            open(VOTERS_FILE, 'w').close()
        
    return jsonify({"success": True, "votes": votes})

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    token = request.headers.get('Authorization', '').strip()
    if token != RESET_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    votes = load_votes()
    meta = load_meta()
    
    ip_count = 0
    if os.path.exists(VOTERS_FILE):
        with open(VOTERS_FILE, 'r') as f:
            ip_count = len(f.read().splitlines())

    return jsonify({
        "votes": votes,
        "meta": meta,
        "unique_ips": ip_count
    })

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    app.run(debug=debug_mode, port=5000)
