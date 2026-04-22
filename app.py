import os
import hmac
import hashlib
import base64
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────────────
#  Credentials come from Render environment variables
#  Never hardcoded — never in GitHub
# ─────────────────────────────────────────────────────
PAT_TOKEN      = os.environ.get("LC_PAT_TOKEN", "")
ACCOUNT_ID     = os.environ.get("LC_ACCOUNT_ID", "")
BOT_AGENT_ID   = os.environ.get("LC_BOT_AGENT_ID", "")
WEBHOOK_SECRET = os.environ.get("LC_WEBHOOK_SECRET", "")

LC_API_URL = "https://api.livechatinc.com/v3.5/agent/action"


def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify request came from LiveChat."""
    if not WEBHOOK_SECRET:
        return True
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def send_reply(chat_id: str, message: str):
    """Send reply back into LiveChat chat."""
    credentials = base64.b64encode(
        f"{ACCOUNT_ID}:{PAT_TOKEN}".encode()
    ).decode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {credentials}",
        "X-Author-Id": BOT_AGENT_ID,
    }

    payload = {
        "chat_id": chat_id,
        "event": {
            "type": "message",
            "text": message,
            "visibility": "all",
        }
    }

    response = requests.post(
        f"{LC_API_URL}/send_event",
        json=payload,
        headers=headers
    )

    print(f"  → Reply sent | status: {response.status_code}")
    if response.status_code != 200:
        print(f"  → Error: {response.text}")
    return response


def get_reply(customer_message: str) -> str:
    """
    ── BOT BRAIN ─────────────────────────────────────
    Hardcoded test replies for now.
    Later: replace this function with Claude API call
    or your casino chatbot call.
    ──────────────────────────────────────────────────
    """
    msg = customer_message.lower().strip()

    if any(word in msg for word in ["hello", "hi", "hey"]):
        return "Test 1 ✅ — Hello received! Bot is connected and working."

    if "test" in msg:
        return "Test 2 ✅ — Test message received! Everything looks good."

    if "help" in msg:
        return "Test 3 ✅ — Help request received! Real AI coming soon."

    # Default — echo back anything else
    return f"Test ✅ — Bot received your message: '{customer_message}'"


@app.route("/webhook", methods=["POST"])
def webhook():
    """LiveChat posts all events here."""

    raw_body = request.get_data()
    signature = request.headers.get("X-LiveChat-Signature", "")

    if not verify_signature(raw_body, signature):
        print("  → Invalid signature — rejected")
        return jsonify({"error": "invalid signature"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no data"}), 400

    action = data.get("action", "")
    print(f"\n[LiveChat] Event: {action}")

    # New chat started
    if action == "incoming_chat":
        chat_id = data.get("payload", {}).get("chat", {}).get("id")
        if chat_id:
            print(f"  → New chat started: {chat_id}")
            send_reply(
                chat_id,
                "👋 Hi! I am a test bot. Try saying 'hello', 'test', or 'help'."
            )

    # New message received
    elif action == "incoming_event":
        payload  = data.get("payload", {})
        event    = payload.get("event", {})
        chat_id  = payload.get("chat_id")
        author   = event.get("author_id", "")

        # Only reply to customer messages — ignore bot's own messages
        if event.get("type") == "message" and author != BOT_AGENT_ID:
            customer_message = event.get("text", "")
            print(f"  → Customer said: '{customer_message}'")
            reply = get_reply(customer_message)
            print(f"  → Bot replies: '{reply}'")
            send_reply(chat_id, reply)

    # Always return 200 immediately
    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def health():
    """Health check — also shows if credentials are set correctly."""
    missing = []
    if not PAT_TOKEN:    missing.append("LC_PAT_TOKEN")
    if not ACCOUNT_ID:   missing.append("LC_ACCOUNT_ID")
    if not BOT_AGENT_ID: missing.append("LC_BOT_AGENT_ID")

    if missing:
        return jsonify({
            "status": "⚠️ running — but missing environment variables",
            "missing_vars": missing,
            "fix": "Add these in Render → Environment → Add Environment Variable"
        }), 200

    return jsonify({
        "status": "✅ Bot is running and ready",
        "account_id": ACCOUNT_ID,
        "bot_agent_id": BOT_AGENT_ID,
        "webhook_endpoint": "/webhook"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
