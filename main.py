from flask import Flask, request, jsonify
import os
import requests
import time
import uuid

app = Flask(__name__)

@app.route("/", methods=["GET"])
def root():
    return "Jarvis is online.", 200

@app.route("/v1/chat/completions", methods=["POST"])
def elevenlabs_llm():
    data = request.get_json()
    print("🟡 Incoming JSON from ElevenLabs:", data)

    try:
        prompt = data["messages"][-1]["content"]
    except Exception:
        return (
            jsonify({"error": "Invalid message format"}),
            400,
            {'Content-Type': 'application/json'}
        )

    model = data.get("model", "llama3-8b-8192")

    try:
        groq_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt + "\n\nRespond in 2–3 sentences max."}],
                "temperature": 0.7,
                "max_tokens": 200
            },
            timeout=5
        )

        result = groq_response.json()
        reply = result["choices"][0]["message"]["content"].strip()

        # Optional: Truncate if somehow still too long
        if len(reply) > 400:
            reply = reply[:400] + "..."

        print("🟢 Groq reply (trimmed):", reply[:300] + ("..." if len(reply) > 300 else ""))

        return (
            jsonify({
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
            }),
            200,
            {'Content-Type': 'application/json'}
        )

    except Exception as e:
        print("🔴 Groq parse error:", e)
        return (
            jsonify({
                "id": f"chatcmpl-error-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Jarvis encountered a brain glitch. Please retry."
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }),
            200,
            {'Content-Type': 'application/json'}
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
