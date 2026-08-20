# Email agent on Replit

An agent with its own email address. Mail arrives, Claude reads the thread, the
reply goes back in the same conversation.

[![Run on Replit](https://replit.com/badge/github/UseCarly/carlyemail-examples)](https://replit.com/github/UseCarly/carlyemail-examples)

## Why this one is on Replit

Every other quickstart stalls at the same place. Inbound mail needs a public
HTTPS URL, and getting one on your laptop means ngrok, or a deploy, or a tunnel
that dies when you close the lid. Replit gives you one for free, and the repl
can read its own URL out of the environment — so the webhook wires itself up
and there is nothing to paste anywhere.

## Setup

1. Click **Run on Replit** above.
2. Add two Secrets in the sidebar:
   - `CARLYEMAIL_API_KEY` — from `npx carlyemail signup --human-email you@example.com --username assistant`
   - `ANTHROPIC_API_KEY`
3. Press **Run**.

The console prints the address it is listening on:

```
  Ready.
  Inbox:   assistant@carlyemail.com
  Webhook: https://your-repl.replit.dev/webhook

  Send mail to assistant@carlyemail.com and it will reply.
```

Send it an email.

## What happens on boot

`bootstrap.py` runs before the server accepts anything:

1. Works out the repl's public URL — `REPLIT_DOMAINS` in a deployment,
   `REPLIT_DEV_DOMAIN` in the workspace, `PUBLIC_URL` if you set it.
2. Finds an inbox — `CARLYEMAIL_INBOX` if set, otherwise the first on the
   account, otherwise creates one.
3. Deletes webhooks this template created on a previous boot, then registers a
   fresh one pointing at this URL.

Step 3 recreates the webhook every time rather than reusing it, because the
signing secret is returned once at creation and is only ever held in memory.
That also handles Replit handing out a new dev URL each session — stale
webhooks are matched by `client_id`, not by URL, so ones pointing at hostnames
that no longer exist still get cleaned up.

If any of that fails the server refuses to start and says why. A server that
starts but never receives mail is worse to debug than one that won't boot.

## Settings

Everything below is optional.

| Secret | Default | What it does |
|---|---|---|
| `CARLYEMAIL_INBOX` | first inbox on the account | Which mailbox to answer on |
| `ALLOWED_SENDERS` | empty — anyone | Comma-separated. `you@example.com` or `@yourcompany.com` for a whole domain |
| `PUBLIC_URL` | discovered | Set only outside Replit, or on a custom domain |
| `CARLYEMAIL_BASE_URL` | `https://api.carlyemail.com` | Point at another deployment |

Set `ALLOWED_SENDERS` before you give the address to anyone. Without it, anybody
who learns the address can put work in front of the model on your API key.

## What it refuses to do

All of this is [`carlyemail.inbound`](https://docs.carlyemail.com/guides/receiving#the-receiver)
rather than code in this template. `main.py` calls `decide()` directly instead
of mounting the router, because the signing secret does not exist until
`setup()` has registered the webhook.

- **Unsigned deliveries get a 401.** Every delivery is signed; that signature is
  the only reason to believe a request came from CarlyEmail rather than from
  someone who found the URL.
- **Mail that failed authentication never arrives.** The webhook subscribes to
  `message.received` alone, and the receiver admits that event type alone. Mail
  failing SPF, DKIM or DMARC is emitted as `message.received.unauthenticated`
  and spam as `message.received.spam` — different event types, so a forged
  sender never reaches the handler. This is what makes `ALLOWED_SENDERS`
  meaningful; a `From` header on its own can say anything.
- **The inbox does not answer itself.** An alias or a mailing list can loop a
  reply back round, and an agent answering itself does not stop on its own.
- **Redeliveries are dropped.** Delivery is at least once, so the same
  `event_id` is only acted on the first time. The guard is in memory and
  bounded, so it resets when the repl restarts.

## Moving off the dev URL

The workspace URL sleeps when the repl does, and mail that arrives while it is
asleep is retried rather than lost — CarlyEmail retries for up to 24 hours, and
[the event log](https://docs.carlyemail.com/guides/events) is the backfill path
for anything that exhausts its retries.

For something that stays up, hit **Deploy**. `REPLIT_DOMAINS` is set in
deployments too, so the same bootstrap runs and re-points the webhook at the
deployment's URL with no changes.

## Running it elsewhere

Nothing here is Replit-specific except the URL discovery. Set `PUBLIC_URL` and
`python main.py` works anywhere with a public hostname.
