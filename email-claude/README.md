# Email Claude

> You write to an address. Claude answers.

No persona, no tools, nothing to configure: the entire email integration with
nothing else in the way. Read it first.

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

Claude holds no tools, so the worst an instruction inside an email can do is
change the words of one reply to the person who sent it. What it does still
cost is tokens — set `ALLOWED_SENDERS` unless the address is meant to be
public.

The email half is covered by `tests/`; the model call has not been run here
yet.
