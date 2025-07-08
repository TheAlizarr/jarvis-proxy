from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route("/v1/chat/completions", methods=["POST"])
def elevenlabs_llm():
    data = request.get_json()

    # Extract the user prompt from the messages list
    prompt = ""
    try:
        prompt = data["messages"][-1]["content"]
    except Exception:
        return jsonify({"error": "Invalid message format"}), 400

    model = data.get("model", "llama3-8b-8192")

    groq_response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )

    try:
        result = groq_response.json()
        reply = result["choices"][0]["message"]["content"]
        # Match OpenAI format so ElevenLabs accepts it
        return jsonify({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": reply
                    }
                }
            ]
        })
    except Exception as e:
        print("Groq parse error:", e)
        return jsonify({
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Sorry, I couldn't think fast enough."
                    }
                }
            ]
        }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
