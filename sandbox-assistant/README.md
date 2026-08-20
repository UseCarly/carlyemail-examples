# Sandbox assistant

> Email it a task. Claude does it in a sandbox and replies.

The agent runs on Anthropic's Managed Agents, with a shell, a filesystem and
the web, on your Anthropic account.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=assistant@carlyemail.com
python setup.py            # once: creates the agent, prints two ids
export ANTHROPIC_AGENT_ID=... ANTHROPIC_ENVIRONMENT_ID=...
uvicorn webhook:app --port 8080
```

Set `ALLOWED_SENDERS` before you share the address. It reaches a shell.
