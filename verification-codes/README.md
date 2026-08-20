# Verification codes

An address your agent can sign up for things with. Most sign-ups end with
"we emailed you a code"; an agent with an inbox reads it and carries on.

```python
from carlyemail import CarlyEmail
from codes import wait_for_code

carly = CarlyEmail()                                    # reads CARLYEMAIL_API_KEY
inbox = carly.inboxes.create({"username": "signups"})   # signups@carlyemail.com

# ... your agent fills in a form with inbox["email"] ...

code = wait_for_code(carly, inbox["email"], sender="@github.com", timeout=120)
code.value                                              # "482913"
```

`codes.py` is the whole thing: no model, and about ninety lines worth
copying once you drop the module docstring and the `python codes.py` block
at the bottom. Copy it into the agent that needs it.

## What it gets right

- **Only mail that arrives after you ask.** A code from an earlier attempt is
  still sitting in the inbox; this ignores it.
- **Only the sender you name.** An inbox that signs up for three things at once
  holds three codes. `sender="@github.com"` or `sender="noreply@github.com"`.
- **The code, not the order number.** It looks for digits next to words like
  *code*, *verify*, *one-time*, and prefers six-digit runs, so `Order #48211 …
  confirm with code 557201` gives `557201`.
- **A timeout, not a guess.** If nothing comes, it raises.

## Run it

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=signups@carlyemail.com
python codes.py @github.com        # waits, prints the code
```

## Run for real

2026-08-20. A sign-up confirmation was sent from `tom.reyes@carlyemail.com` to
`lena.okafor@carlyemail.com` three seconds after `wait_for_code` started
polling, with this body:

> Your Northwind Dispatch verification code is 482913. It expires in 10 minutes.
>
> If you did not request this, ignore this email. Order #77120 is unaffected.

`wait_for_code(carly, inbox, sender="@carlyemail.com")` returned 6.5 seconds
after it was called:

```
code 482913 from 'tom.reyes@carlyemail.com' subject 'Your Northwind verification code'
```

`482913`, not `77120`: the order number sits next to no code-shaped word.
The unit tests in `tests/test_codes.py` cover the other shapes — two digit
groups, a four-digit code, digits with no code words at all.

## The address itself

Every CarlyEmail inbox is a real deliverable address with SPF, DKIM and DMARC,
so sign-up forms accept it and the code arrives within seconds. Create one per
sign-up if you want them disposable — `inboxes.create` takes a `client_id` so a
retry returns the same inbox rather than a second one — or keep one `signups@`
and filter by sender.

The mail a site sends is untrusted input like any other. This reads a number out
of it and nothing else: no links are followed, no instructions are obeyed.
