# Your framework, wired to an inbox

The smallest useful email agent, once per framework: it reads what arrived,
answers what it can answer from the thread, and writes a draft — instead of
sending — when the request needs a commitment it cannot verify. Start here to
see how *your* framework connects; the examples in the parent directory are
what you build once it does.

The same job three times, in three frameworks. The CarlyEmail half is identical
in all of them — one hosted MCP server, no tool wrappers to write or keep in
step with the API — so the diff between the directories is the framework, not
the integration.

| Variant | Framework | Model auth |
|---|---|---|
| [`openai/`](openai) | OpenAI Agents SDK | `OPENAI_API_KEY` |
| [`langchain/`](langchain) | LangChain + LangGraph | `OPENAI_API_KEY` |
| [`claude/`](claude) | Claude Agent SDK | your signed-in `claude` CLI |

## Run it

```bash
cd openai        # or langchain, or claude
pip install -r requirements.txt
cp .env.example .env   # fill it in
python agent.py
```

`agent.py` does one pass of the inbox. `webhook.py` is the same agent woken by
CarlyEmail when mail actually arrives — see the comments in it for what the
receiver checks before your agent spends a token.

## Run for real, 2026-08-20

Each variant was run against a live inbox, `support-inbox@agents.carlyemail.com`,
seeded with the same two emails: an answerable question ("is this the right
address for monthly invoices?" — Tom Hewitt) and a request for a commitment
("approve a $189 refund today" — Lena Fischer).

All three did the job asked: replied to Tom on his thread, and left Lena's
refund as a draft rather than sending, because approving $189 is not the
agent's call. The OpenAI variant's actual reply:

> Yes — this address (support-inbox@agents.carlyemail.com) is fine for monthly
> invoices. If you'd prefer a dedicated billing inbox, let me know and I can
> confirm one.

and the Claude variant's actual draft, left unsent on Lena's thread:

> I've noted that you'd prefer a full refund of $189 rather than a replacement,
> and I've passed your request on for approval. I'll confirm with you as soon
> as it has been signed off, along with how and when the refund will reach you.

Two things went wrong across the runs, and both are now rules in the prompts —
worth keeping if you adapt this:

- **The LangChain run invented a recipient.** It drafted the refund escalation
  to `refunds@carlyemail.com`, an address nobody gave it. Nothing failed; a
  plausible-looking draft simply sat addressed to a mailbox that does not
  exist. Hence the prompt rule: a draft is a *reply* (`in_reply_to` the
  message), never mail to an address the thread did not name. The boundary
  that actually holds is the key, not the prompt — an
  [inbox-scoped key](https://docs.carlyemail.com/authentication) without
  `message_send` cannot mail anyone new regardless.
- **The first run read beyond its mailbox.** With an organization-wide key,
  `list_messages` without `inbox_id` reads every inbox the key can reach, and
  the agent noticed another mailbox's mail. The prompts now pin `inbox_id` on
  every call; an inbox-scoped key makes the mistake impossible.

Also honest: the seed mail was sent from `sarah@carlyemail.com` with personas
in the body, and the Claude variant flagged the mismatch unprompted ("both
messages show From: sarah@… despite being signed by Lena and Tom"). Replies go
to the real sender, not the signature.

## Positions these examples take

- **A named tool allowlist, not a wildcard.** CarlyEmail serves 28 tools; these
  agents hold five. The body of an email is written by a stranger, and an agent
  reading strangers' mail should not be holding `delete_thread`.
- **Draft when it matters.** A price, a date, an approval — anything about
  money or authority becomes a draft a person can send, edit, or delete.
- **Reply, never compose.** `reply_to_message` lands in the sender's thread;
  a fresh message starts a second conversation.
- **Filter to `received`.** Without it the agent also lists its own sent mail,
  and answers itself.
- **Read `extracted_text`.** It is the new message with the quoted chain
  stripped — what the model should see.
