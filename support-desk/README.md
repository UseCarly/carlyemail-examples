# Support desk

> Answers from your docs. Escalates the rest to a person.

A support inbox run by an agent. For each email it:

- **Answers** from your documentation, citing the page — or
- **Escalates** to a person: forwards the thread with a summary of what was
  asked and what it already checked, tells the customer who has it, and
  schedules a reminder for a day later
- **Relays** the person's reply back to the customer when it arrives, and
  cancels the reminder
- **Labels** every thread: `how-to` `bug` `billing` `outage` `urgent`
  `needs-human`

Built on the OpenAI Agents SDK and
[`carlyemail-toolkit`](https://docs.carlyemail.com/integrations/toolkit).

## What you need

- A CarlyEmail key and inbox — `npx carlyemail signup`
- An OpenAI key
- Docs that serve `llms.txt` and Markdown pages (`DOCS`), and a person's
  address for escalations (`HUMAN`)

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # one pass
uvicorn webhook:app --port 8080   # or: run when mail arrives
```

## How it works

1. The agent reads the thread, reads your docs, checks the customer's
   history, and decides: reply or escalate.
2. On escalate, code forwards the thread to `HUMAN` with a summary, labels
   it `needs-human`, schedules a reminder, and tells the customer.
3. When `HUMAN` replies to the forward, the next pass writes their answer
   up as a reply to the customer and cancels the reminder.

## Customize

- `DOCS`, `PRODUCT` — your docs and your name.
- `NUDGE_AFTER` in `agent.py` — how long a person gets before the reminder.
- `TRIAGE_INSTRUCTIONS` — tone, and what counts as needing a person.
