# CarlyEmail examples

Agents with a real email address. Clone one, add two keys, run it.

| | |
|---|---|
| [**Coding agent**](coding-agent) | Email it a task about a repo. It opens a pull request and replies with the link. Claude Agent SDK. |
| [**Support desk**](support-desk) | Answers support mail from your docs. Escalates the rest to a person, and relays the answer back. OpenAI Agents SDK. |
| [**Verification codes**](verification-codes) | An address your agent signs up for things with. It reads the code the site emails. |

Also: the smallest agent on each framework in [`frameworks/`](frameworks),
[`email-claude/`](email-claude), [`sandbox-assistant/`](sandbox-assistant),
and a one-click [`replit-email-agent/`](replit-email-agent).

## Quick start

```bash
npx carlyemail signup --human-email you@yourcompany.com --username assistant
npx carlyemail verify 123456            # the code from your email

cd support-desk
pip install -r requirements.txt
cp .env.example .env
python agent.py
```

Each example has an `agent.py` (runs once over the inbox) and a `webhook.py`
(runs whenever mail arrives).

## License

MIT.
