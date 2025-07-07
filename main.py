from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# You can set this in the Replit Secrets tab for security
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "your_groq_api_key_here"  # Replace this for testing only
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

@app.route("/", methods=["GET"])
def home():
    return "✅ Flask server is running! Use POST /chat to send prompts.", 200

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_prompt = data.get("prompt")

    if not user_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Make request to Groq API
    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are Jarvis, a smart and witty assistant."},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }
    )

    if response.status_code != 200:
        return jsonify({"error": "Groq API request failed", "details": response.text}), 500

    result = response.json()
    reply = result["choices"][0]["message"]["content"]
    return jsonify({"response": reply}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
