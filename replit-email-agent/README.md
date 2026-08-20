# Email agent on Replit

> One click. An agent that answers its mail.

Claude reads each email and replies on the thread. Replit gives it a public
URL, and the repl sets up its own webhook.

[![Run on Replit](https://replit.com/badge/github/UseCarly/carlyemail-examples)](https://replit.com/github/UseCarly/carlyemail-examples)

## Setup

1. Click **Run on Replit**.
2. Add two Secrets: `CARLYEMAIL_API_KEY` (from `npx carlyemail signup`) and
   `ANTHROPIC_API_KEY`.
3. Press **Run**. The console prints the address. Send it an email.

## Settings

| Secret | Default | |
|---|---|---|
| `CARLYEMAIL_INBOX` | first inbox on the account | Which mailbox to answer on |
| `ALLOWED_SENDERS` | anyone | `you@example.com` or `@yourcompany.com` |

Set `ALLOWED_SENDERS` before you share the address. Hit **Deploy** for a URL
that stays up when the workspace sleeps.
