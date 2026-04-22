# LiveChat Test Bot — Render Deployment

## What this does
- Receives messages from LiveChat customers via webhook
- Replies with test responses (hello/test/help)
- Ready to swap in real AI later with one function change

---

## STEP 1 — Upload to GitHub

1. Go to github.com → sign in → click New repository
2. Name it: livechat-test-bot
3. Set to Public
4. Click Create repository
5. Upload these 4 files (drag and drop):
   - app.py
   - requirements.txt
   - render.yaml
   - .gitignore
6. Click Commit changes

NOTE: Do NOT upload any .env file — credentials go directly into Render.

---

## STEP 2 — Deploy on Render

1. Go to render.com → sign up free with GitHub account
2. Click New → Web Service
3. Click Connect a repository → select livechat-test-bot
4. Render auto-detects settings from render.yaml
5. Scroll down to Environment Variables → Add these 4:

   LC_PAT_TOKEN      → your PAT token
   LC_ACCOUNT_ID     → your Account ID
   LC_BOT_AGENT_ID   → your Bot Agent ID
   LC_WEBHOOK_SECRET → mysecrettest123

6. Click Create Web Service
7. Wait 2-3 minutes for it to build
8. Copy your live URL — looks like:
   https://livechat-test-bot.onrender.com

---

## STEP 3 — Verify it is running

Open your Render URL in a browser:
https://livechat-test-bot.onrender.com

You should see:
{
  "status": "✅ Bot is running and ready",
  "account_id": "your-account-id",
  "bot_agent_id": "your-bot-agent-id",
  "webhook_endpoint": "/webhook"
}

If you see missing_vars — go back to Render environment variables and fix them.

---

## STEP 4 — Create Bot Agent (if not done yet)

You need a Bot Agent ID before the bot can send messages.
Use Hoppscotch (hoppscotch.io) — free, runs in browser:

Method:  POST
URL:     https://api.livechatinc.com/v3.5/configuration/action/create_bot
Header:  Authorization: Basic <base64 of ACCOUNT_ID:PAT_TOKEN>
Header:  Content-Type: application/json
Body:    {"name": "My Test Bot", "status": "accepting chats"}

To get your base64 string:
1. Go to base64encode.org
2. Encode this exact string: yourAccountID:yourPATtoken
3. Copy result and paste after "Basic " in the header

Response gives you the bot ID — copy it into Render environment variables as LC_BOT_AGENT_ID.
Then redeploy on Render (it redeploys automatically when env vars change).

---

## STEP 5 — Set webhook URL in LiveChat Developer Console

1. Go to developers.livechat.com/console
2. Open your app → Building Blocks → Chat webhooks
3. Webhook URL: https://livechat-test-bot.onrender.com/webhook
4. Secret key: mysecrettest123
5. Triggers: check incoming_chat and incoming_event
6. Save
7. Go to Private Installation tab → click Install

---

## STEP 6 — Assign bot as agent in LiveChat

1. Go to my.livechat.com
2. Settings → Team → Groups → General → Edit
3. Add My Test Bot as Primary agent
4. Add yourself as Backup agent
5. Save

---

## STEP 7 — Test it

1. Go to my.livechat.com → Settings → Chat Widget → Preview
2. Type: hello  → expect: Test 1 ✅
3. Type: test   → expect: Test 2 ✅
4. Type: help   → expect: Test 3 ✅
5. Type anything else → bot echoes it back

Check Render logs in real time:
Render dashboard → your service → Logs tab

---

## Adding real AI later (one change only)

In app.py find the get_reply() function and replace with:

    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def get_reply(customer_message: str) -> str:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="You are a helpful casino support assistant.",
            messages=[{"role": "user", "content": customer_message}]
        )
        return message.content[0].text

Then add ANTHROPIC_API_KEY to Render environment variables.
Everything else stays exactly the same.

---

## Troubleshooting

Bot not replying?
  - Check Render logs for errors
  - Make sure app is installed in Developer Console
  - Confirm all 4 environment variables are set in Render
  - Make sure Bot Agent is set as Primary in LiveChat group

Getting 401 errors?
  - PAT token may have wrong scopes — needs chats--all:rw and agents-bot--all:rw
  - Recreate PAT with correct scopes

Render sleeping?
  - Free tier sleeps after 15 min of inactivity
  - First message after sleep takes 30-60 sec to respond
  - Upgrade to $7/mo paid tier for always-on
