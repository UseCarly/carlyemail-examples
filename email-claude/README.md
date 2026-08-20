# Email Claude

You write to an address, Claude answers — the way it would in a chat window,
delivered as email, on the thread you started. No persona, no tools, nothing to
configure. This is the entire email integration with nothing else in the way,
so read it first.

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=claude@carlyemail.com
export ANTHROPIC_API_KEY=sk-ant-...
export ALLOWED_SENDERS=you@yourcompany.com
python listen.py
```

Three files:

| | |
|---|---|
| `reply.py` | Reads the thread, asks Claude, replies. Everything that is *the job*. |
| `listen.py` | Learns that mail arrived over a WebSocket. No public URL, no webhook, no secret — use it while building, or on any long-lived process. |
| `webhook.py` | Learns the same thing from a signed HTTP callback. Use it in production, on serverless or durable runtimes. |

The two ways of being told share `answer()` and differ only in plumbing.

## Why it holds no tools

Claude here cannot read another mailbox, send anywhere else, or spend money,
because nothing in `reply.py` gives it a way to. The worst an instruction
buried in an email can do is change the words of one reply to the person who
sent it. The examples with tools have to earn that with allowlists and scoped
keys; this one gets it by having nothing to take away.

What it does still cost is tokens, so set `ALLOWED_SENDERS` unless the address
is meant to be public. Empty allows anybody.

## Run for real

Not yet. There was no Anthropic key to hand on 2026-08-20, when the rest of
this repository was run. The email half — signature verification, the event
filter, dropping the mailbox's own sends, sender allowlist, redelivery
de-duplication — is exercised by `tests/test_webhooks.py` against real signed
deliveries. The model call in the middle is the unverified part.
