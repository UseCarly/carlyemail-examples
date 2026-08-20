# Support desk

> Answers from your docs. Escalates the rest to a person.

A support inbox run by an agent. For each email it either:

- **Answers** from your documentation, linking the page, or
- **Escalates**: forwards the thread to a person with a summary, tells the
  customer someone has it, and reminds the person if they go quiet

When the person replies, the desk passes their answer back to the customer.
Every thread gets a label: `how-to` `bug` `billing` `outage` `urgent`
`needs-human`.

Built on the OpenAI Agents SDK and
[`carlyemail-toolkit`](https://docs.carlyemail.com/integrations/toolkit).

## What you need

- A CarlyEmail key and inbox — `npx carlyemail signup`
- An OpenAI key
- Your docs URL (`DOCS`) and the person escalations go to (`HUMAN`)

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # run once
uvicorn webhook:app --port 8080   # or run whenever mail arrives
```

## How it works

1. The agent reads the thread and your docs, checks whether the customer
   has written before, and decides: answer or escalate.
2. Escalations are forwarded to `HUMAN`. Replying to the forward is all the
   person has to do.
3. Anything about money, outages, or angry customers goes to a person.
   So does anything the docs don't cover.

## Customize

- `DOCS`, `PRODUCT` — your docs and your name.
- `NUDGE_AFTER` — how long before the person gets a reminder. Default a day.
- `TRIAGE_INSTRUCTIONS` in `agent.py` — tone, and what needs a person.
