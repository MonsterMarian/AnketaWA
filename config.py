import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESET_TOKEN = os.environ.get("ADMIN_TOKEN", "super-tajny-token-123")
VOTE_FILE = os.path.join(BASE_DIR, "data", "votes.json")
QUESTIONS = {
    "question": "Kolik otevřených záložek v prohlížeči je ještě normální?",
    "options": [
        {"id": "0-5", "label": "0-5 (Minimalista)"},
        {"id": "6-20", "label": "6-20 (Běžný uživatel)"},
        {"id": "21+", "label": "21+ (Chaotik)"},
        {"id": "melt", "label": "Můj prohlížeč už taje"}
    ]
}
