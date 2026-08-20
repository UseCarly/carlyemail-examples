# Coding agent

> Email it a task. Get a pull request back.

A coding agent whose only interface is email. It clones the repository, makes
the change on a branch, opens a pull request, and replies on your thread with
the link. Reply on the thread and it resumes the same session — same working
copy, same context.

Built on the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview).

## What you need

- A CarlyEmail key and inbox — `npx carlyemail signup`
- An Anthropic key
- `gh` logged in as the identity that should open the pull requests
- `ALLOWED_SENDERS` (who may give it work) and `ALLOWED_REPOS` (where) — both
  required

```bash
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # one pass
uvicorn webhook:app --port 8080   # or: run when mail arrives
```

## How it works

1. A task arrives from an allowed sender naming an allowed repository.
2. The agent gets a working directory for the thread, a shell, file tools,
   and a PreToolUse hook that refuses pushes to main, force pushes, `rm -rf`
   outside the working copy, `sudo`, and clones of any other repository.
3. It branches, makes the change, runs the tests, pushes, opens the PR, and
   its final message is the reply.
4. The session id is stored as a label on the thread, so the next message
   resumes it.

Mail from anyone else is not read and not answered.

## It ran

> **Task:** In our examples repo, verification-codes/README.md says codes.py
> is "Sixty lines, no model". It isn't. Count the actual lines, fix the claim
> wherever it appears, and open a PR.
>
> **Agent, 99 s later:** `codes.py` is 144 lines, so that's what both READMEs
> now say. The PR is [link]. One thing worth flagging: 144 is the whole file,
> docstring and `__main__` block included … the copyable part is really the
> ~90 lines of `extract`, `wait_for_code` and `_from`. If you'd rather the
> README made that distinction, say the word. While I was in there I noticed
> `sandbox-assistant/webhook.py` makes a similar claim about itself.
>
> **Reply on the thread:** Good catch on both. Reword it your way — say the
> part worth copying is about ninety lines — and fix the sandbox-assistant
> claim too, same PR.
>
> **Agent, resumed:** Both reworded, on the same PR. Before writing "ninety"
> anywhere I measured it rather than reusing my own estimate … the claim
> appeared in four places, not the two I reported last time.

Two commits on one pull request, +6/−5, merged.

## Customize

- `ALLOWED_REPOS` is the blast radius. Start with one.
- `MAX_TURNS` (default 60) is the budget per task.
- The rules in `SYSTEM_PROMPT` — branch, never main; ask rather than guess —
  are the ones that held. Keep them.
