# Coding agent

> Email it a task. Get a pull request back.

It clones the repo, makes the change on a branch, opens a pull request, and
replies with the link. Reply on the thread and it continues where it left
off.

Built on the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview).

## What you need

- A CarlyEmail key and inbox — `npx carlyemail signup`
- An Anthropic key
- `gh` logged in
- `ALLOWED_SENDERS` — who can give it work
- `ALLOWED_REPOS` — which repos it can work in

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # run once
uvicorn webhook:app --port 8080   # or run whenever mail arrives
```

## How it works

1. A task arrives from someone on `ALLOWED_SENDERS`, naming a repo on
   `ALLOWED_REPOS`. Anyone else is ignored.
2. The agent clones it, branches, makes the change, runs the tests, opens
   the PR. It can't push to main or touch other repos.
3. Its summary is the reply. The thread is the session.

## Customize

- `ALLOWED_REPOS` — start with one.
- `MAX_TURNS` — how much work one task can take. Default 60.
- `SYSTEM_PROMPT` in `agent.py` — how it works.
