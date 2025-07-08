from flask import Flask, request, jsonify
import os
import requests
import uuid
import time
import re

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Jarvis LLM proxy is live!", 200

@app.route("/v1/chat/completions", methods=["POST"])
def handle_completion():
    data = request.get_json()
    print("🟡 Incoming from ElevenLabs:", data)

    # Extract safe defaults
    model = data.get("model", "llama3-8b-8192")
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 200)

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "Invalid or missing messages list."}), 400

    prompt = messages[-1].get("content", "")
    if not prompt.strip():
        return jsonify({"error": "Empty prompt"}), 400

    # Send to Groq
    try:
        groq_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=5
        )
        groq_response.raise_for_status()
        gr = groq_response.json()
        print("🟢 Groq response received.")

        reply = gr["choices"][0]["message"]["content"].strip()

        # Clean and truncate for speech
        reply = re.sub(r"[`*_~#]", "", reply)
        if len(reply) > 400:
            reply = reply[:400] + "..."

        usage = gr.get("usage", {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        })

        result = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply
                },
                "finish_reason": "stop"
            }],
            "usage": usage
        }

        print("✅ Reply to ElevenLabs:", reply)
        return jsonify(result), 200, {"Content-Type": "application/json"}

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({
            "id": f"chatcmpl-error-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Sorry, something went wrong in Jarvis's mind."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }), 200, {"Content-Type": "application/json"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
