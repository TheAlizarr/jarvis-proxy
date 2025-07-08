from flask import Flask, request, jsonify
import os
import requests
import time
import uuid

app = Flask(__name__)

@app.route("/v1/chat/completions", methods=["POST"])
def elevenlabs_llm():
    data = request.get_json()

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

        return jsonify({
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 9,
                "total_tokens": 19
            }
        })

    except Exception as e:
        print("Groq parse error:", e)
        return jsonify({
            "id": f"chatcmpl-error-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Sorry, something went wrong in my brain."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
