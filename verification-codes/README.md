# Verification codes

> An address your agent signs up for things with.

Most sign-ups end with "we emailed you a code". Give the agent an inbox and
it reads the code itself.

```python
from carlyemail import CarlyEmail
from codes import wait_for_code

carly = CarlyEmail()
inbox = carly.inboxes.create({"username": "signups"})

# ... your agent fills in a form with inbox["email"] ...

code = wait_for_code(carly, inbox["email"], sender="@github.com")
code.value                                              # "482913"
```

`codes.py` is the whole thing. No model. Copy it into your agent.

## What it does

- Waits for a new email from the sender you name
- Picks out the code, not the order number
- Gives up after `timeout` seconds

## Run it

```bash
pip install -r requirements.txt
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=signups@carlyemail.com
python codes.py @github.com        # waits, prints the code
```
