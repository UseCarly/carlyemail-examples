# Verification codes

> An address your agent signs up for things with.

Most sign-ups end with "we emailed you a code". An agent with an inbox reads
it and carries on.

```python
from carlyemail import CarlyEmail
from codes import wait_for_code

carly = CarlyEmail()
inbox = carly.inboxes.create({"username": "signups"})

# ... your agent fills in a form with inbox["email"] ...

code = wait_for_code(carly, inbox["email"], sender="@github.com")
code.value                                              # "482913"
```

`codes.py` is the whole thing. No model. Copy it into the agent that needs
it.

## What it gets right

- Only mail that arrived **after you asked** — not a code from an earlier try
- Only the **sender you name**, by address or domain
- The **code, not the order number**: digits next to words like *code*,
  *verify*, *one-time*, six-digit runs preferred
- A **timeout**, not a guess

## Run it

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=signups@carlyemail.com
python codes.py @github.com        # waits, prints the code
```

## It ran

A sign-up email — *"Your Northwind Dispatch verification code is 482913. It
expires in 10 minutes. … Order #77120 is unaffected."* — arrived three seconds
after `wait_for_code` started polling. It returned `482913` 6.5 s after the
call. Tests in `tests/test_codes.py` cover the other shapes.
