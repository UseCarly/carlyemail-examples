# Email Claude

> You write to an address. Claude answers.

No tools, no persona, nothing to configure.

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=claude@carlyemail.com
export ANTHROPIC_API_KEY=sk-ant-...
export ALLOWED_SENDERS=you@yourcompany.com
python listen.py
```

`listen.py` runs on your laptop. `webhook.py` is the same thing for a
server. Set `ALLOWED_SENDERS` unless the address is meant to be public.
