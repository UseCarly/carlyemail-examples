# Sandbox assistant

> Email it a task. A Claude agent with a shell does it and replies.

The agent runs on Anthropic's Managed Agents, in a sandbox with a shell, a
filesystem and the web, on your Anthropic account. The address is the whole
interface.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=assistant@carlyemail.com
python setup.py            # once: creates the agent and its sandbox, prints two ids
export ANTHROPIC_AGENT_ID=... ANTHROPIC_ENVIRONMENT_ID=...
uvicorn webhook:app --port 8080
```

| | |
|---|---|
| CarlyEmail | Receives the mail, delivers a signed event, sends the reply. |
| Anthropic | Runs the agent loop and hosts the sandbox. |
| You | Run `webhook.py` and hold both keys. Neither vendor sees the other's. |

An address that reaches a shell is a public endpoint until something says
otherwise: set `ALLOWED_SENDERS` before you register the webhook.

The email half is covered by `tests/`; the Managed Agents session has not been
run here yet.
