from flask import Flask, request, jsonify
import os, requests, time, uuid

app = Flask(__name__)

@app.route("/", methods=["GET"])
def root():
    return "Jarvis is online.", 200

@app.route("/v1/chat/completions", methods=["POST"])
def elevenlabs_llm():
    data = request.get_json()
    print("🟡 Incoming from ElevenLabs:", data)

    # Extract parameters safely
    model = data.get("model", "llama3-8b-8192")
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 200)
    # user_id, stream, etc., can be captured if needed

    if not messages:
        return jsonify({"error": "Missing messages"}), 400

    prompt = messages[-1].get("content", "")

    try:
        groq_resp = requests.post(
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
        groq_resp.raise_for_status()
        gr = groq_resp.json()
        reply = gr["choices"][0]["message"]["content"].strip()
        if not reply:
            reply = "Sorry, I didn't think of anything."

        usage = gr.get("usage", {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0})

        return (
            jsonify({
                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop"
                }],
                "usage": usage
            }),
            200,
            {"Content-Type": "application/json"}
        )
    except Exception as e:
        print("🔴 Error calling Groq:", e)
        return (
            jsonify({
                "id": f"chatcmpl-error-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant",
                                "content": "Jarvis had a brain freeze, please say that again."},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}
            }),
            200,
            {"Content-Type": "application/json"}
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)
