# CarlyEmail examples

Agents with a real email address. Clone one, add two keys, run it.

[CarlyEmail](https://docs.carlyemail.com) gives an agent an inbox: send,
receive, reply on the right thread, get woken when mail arrives.

| | |
|---|---|
| [**Coding agent**](coding-agent) | Email it a task about a repo. It opens a pull request and replies with the link; reply on the thread and it carries on. Claude Agent SDK. |
| [**Support desk**](support-desk) | Answers from your docs, citing the page. Escalates the rest to a person with a summary, and relays the answer back. OpenAI Agents SDK. |
| [**Verification codes**](verification-codes) | An address your agent signs up for things with. `wait_for_code()` hands back the code the site emails. No model. |

Wiring, one per framework: [`frameworks/`](frameworks) (OpenAI Agents SDK,
LangChain, Claude Agent SDK over hosted MCP), [`email-claude/`](email-claude),
[`sandbox-assistant/`](sandbox-assistant), [`replit-email-agent/`](replit-email-agent).

## Quick start

```bash
npx carlyemail signup --human-email you@yourcompany.com --username assistant
npx carlyemail verify 123456            # the code from your email

cd support-desk
pip install -r requirements.txt
cp .env.example .env                    # model key, CarlyEmail key, inbox
python agent.py                         # one pass over the inbox
```

Every example has an `agent.py` (one pass) and a `webhook.py` (the same pass
when mail arrives). `tests/` drives each `webhook.py` with real signed
deliveries.

## License

MIT.
