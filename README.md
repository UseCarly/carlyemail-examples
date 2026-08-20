# CarlyEmail examples

Agents with a real email address. Each one here was run for real on the date
in its README, and the README quotes the mail it sent and received.

[CarlyEmail](https://docs.carlyemail.com) gives an agent an inbox: it can send,
receive, reply on the right thread, and be woken when mail arrives. These are
things you can build with that.

| | What it does | Shows off |
|---|---|---|
| [**Support desk**](support-desk) | Answers support mail from the product's own docs, citing the page. Hands the rest to a person with a summary, tells the customer who has it, nudges the person a day later, and relays their answer back. Labels every thread. | Triage you can see in the inbox; escalation that does not die; a prompt injection handled |
| [**Negotiation**](negotiation) | A buyer with a budget and a seller with a floor haggle across a real thread until there is a deal, or there is not. Code enforces the budget, whatever the model is told. | One conversation across many turns; two agents on a neutral protocol |
| [**Approval inbox**](approval-inbox) | The agent never sends on its own. It drafts, emails you the draft, and you reply `send` — or tell it what to change. | Human in the loop with no dashboard; drafts that wait |
| [**Research assistant**](research-assistant) | Email it a question; it searches the web and replies in-thread with the answer and the URLs it used. | A tool list that cannot be talked into mailing a stranger |
| [**Verification codes**](verification-codes) | An address your agent signs up for things with. The site emails a code; `wait_for_code()` hands it back. Sixty lines, no model. | Agents that can complete a sign-up |

Below those, the wiring:

| | |
|---|---|
| [`frameworks/`](frameworks) | The smallest useful email agent, once each on the OpenAI Agents SDK, LangChain and the Claude Agent SDK — over hosted MCP, no tool wrappers. All three run for real. |
| [`email-claude/`](email-claude) | You write, Claude answers. No tools, no persona: the entire integration with nothing in the way. |
| [`sandbox-assistant/`](sandbox-assistant) | Email it a task; a Claude agent with a shell does it in Anthropic's cloud and replies. |
| [`replit-email-agent/`](replit-email-agent) | The same, one click, with the public URL problem solved for you. |

The last three need an Anthropic key and are marked *not run* in their
READMEs. Everything else ran on 2026-08-20.

## Running one

Every directory has a `requirements.txt`, a `.env.example` and a README that
says what to do. An inbox and a key come from sign-up, which emails a code to
the address you give:

```bash
npx carlyemail signup --human-email you@yourcompany.com --username assistant
npx carlyemail verify 123456
```

`python agent.py` does one pass over the inbox. Every example also ships a
`webhook.py` that runs the same pass when mail actually arrives, and
`tests/test_webhooks.py` drives each of those with real signed deliveries: a
valid one reaches the agent once, a forged one gets 401, spam and failed-auth
variants are dropped, the mailbox never answers itself, a redelivery does not
run the agent twice.

## Three things every example does

**Filters to `received`.** `list_messages` returns the mailbox's own sent mail
too. An agent that skips the filter answers itself, forever.

**Reads `extracted_text`, not `text`.** The quoted chain is stripped, so the
model sees the new message and not the whole history again.

**Replies; never composes.** A reply lands in the sender's existing thread. A
new message starts a second one and they see two.

## Two positions they take

**A short tool list, not a wildcard.** Each agent names the tools it holds.
Email is written by strangers, and an agent reading it should not be holding
`delete_thread` when it has no use for it. The limit that actually holds is
an [inbox-scoped API key](https://docs.carlyemail.com/authentication): the
tool list is a preference, the key is a permission.

**Consequences are code.** Where something leaves the thread — a forward, a
send to a new address, an approval, an offer above budget — the model
proposes and code decides, with ids the model never chose. Read the support
desk and the negotiation for the two versions of that.

## Keys

Every example runs wherever you run it, against your own model key; CarlyEmail
never sees it, and the model provider never sees your CarlyEmail key. The ones
here ran on `gpt-5-mini` unless the README says otherwise.
