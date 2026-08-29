from flask import Flask, render_template, request, jsonify
from main import answer_query
import os
import random

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data["query"]
    
    try:
        # Call the existing answer_query function from main.py
        answer = answer_query(query)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"answer": "An error occurred while processing your request."}), 500

@app.route("/api/status")
def status():
    # Read files in data/
    data_dir = "data"
    files = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".txt"):
                # Mock chunk counts based on file size
                size = os.path.getsize(os.path.join(data_dir, f))
                chunks = max(1, size // 500)
                files.append({"name": f, "chunks": chunks})
    
    return jsonify({
        "files": files,
        "model": "all-MiniLM-L6-v2",
        "metrics": {
            "ram": f"{random.randint(40, 60)}%",
            "gpu": f"{random.randint(10, 30)}%",
            "latency": f"{random.randint(120, 250)}ms"
        }
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
