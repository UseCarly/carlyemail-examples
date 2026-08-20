# Support desk

> Answers from your docs. Escalates the rest to a person, and never loses it.

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

1. A triage agent reads the thread, reads the docs (`list_docs`,
   `read_doc`), checks the customer's history, and decides: reply or
   escalate.
2. Code does everything with consequences — forwarding, labelling, the
   reminder, the customer note, the relay — with ids from the message in
   hand. The model never holds `forward_message` or `send_message`.
3. The forward's subject carries the customer thread's id, so the person's
   reply finds its way back with no state but labels.
4. A relay agent turns the person's terse answer into the email the
   customer reads.

## Customize

- `DOCS` and `PRODUCT` make it yours.
- `NUDGE_AFTER` in `agent.py` is how long a person gets before the reminder.
- Give it an [inbox-scoped key](https://docs.carlyemail.com/authentication).
