# Email Claude

> You write to an address. Claude answers.

No persona, no tools, nothing to configure. The smallest possible email agent.

| | |
|---|---|
| `reply.py` | Reads the thread, asks Claude, replies. |
| `listen.py` | Learns that mail arrived over a WebSocket — no public URL, no secret. For building. |
| `webhook.py` | Learns the same from a signed HTTP callback. For production. |

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=claude@carlyemail.com
export ANTHROPIC_API_KEY=sk-ant-...
export ALLOWED_SENDERS=you@yourcompany.com
python listen.py
```

Set `ALLOWED_SENDERS` unless the address is meant to be public — every email
in costs a model call.
