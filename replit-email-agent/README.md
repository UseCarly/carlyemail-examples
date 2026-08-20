# Email agent on Replit

> One click, a public URL, an agent that answers its mail.

Mail arrives, Claude reads the thread, the reply goes back in the same
conversation. Replit gives the webhook a public URL and the repl wires it
up itself, so there is nothing to paste anywhere.

[![Run on Replit](https://replit.com/badge/github/UseCarly/carlyemail-examples)](https://replit.com/github/UseCarly/carlyemail-examples)

## Setup

1. Click **Run on Replit**.
2. Add two Secrets: `CARLYEMAIL_API_KEY` (from `npx carlyemail signup`) and
   `ANTHROPIC_API_KEY`.
3. Press **Run**. The console prints the address:

```
  Ready.
  Inbox:   assistant@carlyemail.com
  Webhook: https://your-repl.replit.dev/webhook

  Send mail to assistant@carlyemail.com and it will reply.
```

## How it works

On boot, `bootstrap.py` finds the repl's public URL, finds or creates an
inbox, and registers a webhook pointing at itself. `main.py` verifies each
delivery, drops spam, mail that failed authentication, the inbox's own sends
and redeliveries, then asks Claude and replies on the thread.

## Settings

| Secret | Default | |
|---|---|---|
| `CARLYEMAIL_INBOX` | first inbox on the account | Which mailbox to answer on |
| `ALLOWED_SENDERS` | anyone | `you@example.com` or `@yourcompany.com` |
| `PUBLIC_URL` | discovered | Set it to run this anywhere else |

Set `ALLOWED_SENDERS` before you give the address to anyone. Hit **Deploy**
for a URL that stays up when the workspace sleeps.
