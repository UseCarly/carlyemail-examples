# Sandbox assistant

Email it a task. A Claude agent with a shell, a filesystem and the web does the
work in Anthropic's cloud and replies with what it found. The address is the
whole interface.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=assistant@carlyemail.com
python setup.py            # once: creates the agent and its sandbox, prints two ids
export ANTHROPIC_AGENT_ID=... ANTHROPIC_ENVIRONMENT_ID=...
uvicorn webhook:app --port 8080
```

Three parties, and it is worth being precise about who runs what:

| | |
|---|---|
| CarlyEmail | Receives the mail, delivers a signed event, sends the reply. |
| Anthropic | Runs the agent loop and hosts the sandbox, on your Anthropic account. |
| You | Run `webhook.py` — about seventy lines — and hold both keys. |

Neither vendor holds the other's credential. The CarlyEmail key is used in
this process after the agent has finished; it is never handed to the sandbox,
so nothing the agent does with untrusted input can reach for it.

`setup.py` runs once on purpose. An agent is a persisted, versioned object:
sessions pin to a version, so you can change the prompt without disturbing
sessions already running. Creating one per email accumulates orphans and pays
the create latency on every message.

## An address that reaches a shell is a public endpoint

Until something says otherwise. Set `ALLOWED_SENDERS` before you register the
webhook, and read [receiving mail](https://docs.carlyemail.com/guides/receiving)
for what the receiver filters out before your code runs — mail that failed SPF,
DKIM or DMARC never reaches it.

## Run for real

Not yet. There was no Anthropic key to hand on 2026-08-20, when the rest of
this repository was run. `tests/test_webhooks.py` drives this `webhook.py` with
real signed deliveries and a stubbed Anthropic client: a valid delivery reaches
the agent once, a forged one gets 401, the mailbox does not answer itself, and
it mails back what the agent wrote and nothing when it wrote nothing. The
Managed Agents session in the middle is the unverified part.
