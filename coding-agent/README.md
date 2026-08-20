# Coding agent

A coding agent whose only interface is email. Send it a task about a
repository; it clones the repository, makes the change on a branch, opens a
pull request, and replies on your thread with the link and what it did. Reply
on that thread and it picks up the same session — same working copy, same
context — and carries on.

Built on the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview),
which is what gives it a shell, file tools and resumable sessions without this
example implementing any of them. The email half is the CarlyEmail SDK.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=dev@carlyemail.com
export ALLOWED_SENDERS=you@yourcompany.com           # required
export ALLOWED_REPOS=yourorg/api,yourorg/web           # required
gh auth status                                         # it clones and opens PRs with gh
python agent.py                                        # one pass over the inbox
```

`webhook.py` runs the same pass when mail arrives. Each thread gets its own
working directory under `WORKDIR` (default `./work`), which is also what makes
a follow-up cheap: the clone is already there.

## What keeps it from being a shell anyone can email

An address that reaches a shell is a public endpoint until something says
otherwise. Three things do, and all three are code rather than prompt:

- **A sender allowlist.** Mail from anyone else is not read, not replied to,
  not labelled — nothing about the mailbox is revealed to them. The process
  refuses to start without one.
- **A repository allowlist.** A task that names no allowed repository is
  answered with the list and nothing is run. A `gh repo clone` of anything
  else is denied mid-run.
- **A PreToolUse hook on Bash** that refuses pushes to main, force pushes,
  `git reset --hard`, `rm -rf` outside the working copy, `sudo`, and the `gh`
  commands that delete things. The agent sees the refusal and its reason and
  works around it the right way — by opening a pull request.

The agent runs with `permission_mode="bypassPermissions"`: nobody is at a
keyboard to approve each command, so the hook, the working directory and the
two allowlists stand in for approval. Give it a CarlyEmail key scoped to its
inbox, and a GitHub identity whose permissions are the ones you would give a
new contributor.

## Sessions, by label

The Claude Agent SDK returns a `session_id` with every result and accepts
`resume=` to continue one. The agent stores that id as a label on the email
thread — `session:c912ae74-…` — so the next message on the thread resumes the
session, and nothing is kept on disk but the working copy. A thread is a
session; that is the whole mapping.

## Run for real

2026-08-20, against the private repository this one is developed in. The
sender was `lena.okafor@carlyemail.com`; the agent ran as `dev@carlyemail.com`
through the developer's own signed-in `claude` CLI (the README above says
`ANTHROPIC_API_KEY`, which is the way to run it for anyone else). Model: the
SDK default. Quoted from the thread.

**Lena:**

> In UseCarly/carlyemail-examples-dev, verification-codes/README.md says codes.py is "Sixty lines, no model". It isn't sixty any more. Count the actual lines of verification-codes/codes.py, fix the claim there and anywhere else in the repo that repeats it (the top-level README table does), and open a PR.

**The agent**, 99 seconds later, 13 turns, $0.76:

> Hi Lena,
>
> `codes.py` is 144 lines, so that's what both READMEs now say. The PR is https://github.com/UseCarly/carlyemail-examples-dev/pull/1.
>
> The claim turned up in exactly the two places you expected and nowhere else — the sentence in `verification-codes/README.md` ("`codes.py` is the whole thing: 144 lines, no model.") and the Verification codes row of the table in the top-level README. I grepped the rest of the repo for other spellings of the same claim and found nothing further.
>
> One thing worth flagging: 144 is the whole file, docstring and `__main__` block included, which is the honest count but reads differently than "sixty" did. The original number was doing rhetorical work — it's short enough to just copy — and 144 doesn't carry that as well even though the copyable part is really the ~90 lines of `extract`, `wait_for_code` and `_from`, with a 20-line docstring and a CLI block around them. If you'd rather the README made that distinction, say the word and I'll reword it; I stuck to the literal count since that's what you asked for.
>
> While I was in there I noticed `sandbox-assistant/webhook.py` makes a similar claim about itself ("you run these fifty lines"). I left it alone since it wasn't in scope, but it may be worth a look.
>
> Tests pass — 110 of them, via the same steps CI runs.

The pull request: branch `email/codes-line-count`, +2/−2, one commit.

**Lena, replying on the thread:**

> Good catch on both. Reword it your way — say the part worth copying is about ninety lines — and fix the sandbox-assistant claim too while you're there, same PR.

**The agent**, resuming the session, 14 turns, $0.78:

> Both reworded, on the same PR: https://github.com/UseCarly/carlyemail-examples-dev/pull/1
>
> Before writing "ninety" anywhere I measured it rather than reusing my own estimate from last time, which turned out to be worth doing. Dropping the module docstring and the `python codes.py` block leaves 111 lines, of which 94 are non-blank and 85 are non-comment code. So ninety is a fair description of the copyable body, and that's the rule I applied to both files: non-blank lines you'd actually paste, docstring and CLI block excluded. The `verification-codes` README now says so explicitly — "about ninety lines worth copying once you drop the module docstring and the `python codes.py` block at the bottom" — and the top-level table row reads "About ninety lines, no model."
>
> The sandbox-assistant claim needed a bigger correction than I expected. On that same measure `webhook.py` is 73 non-blank lines, not fifty, so both mentions now say about seventy. One caveat worth your judgement: `webhook.py` is comment-heavy — 19 of those lines are comments — so on a code-only count it's 54, and the original "fifty" was defensible under that reading. I went with seventy because it's consistent with how `codes.py` is now described, but it's a one-word change if you'd rather both files quote code-only figures instead.
>
> Also, the claim appeared in four places, not the two I reported last time. My first grep missed `sandbox-assistant/README.md` line 23 — "about fifty lines" written as a word and followed by an em dash, which slipped past a pattern expecting digits or a trailing comma. I re-swept with a wider pattern covering spelled-out numbers and confirmed these four are all of them.
>
> Tests still pass, 110 of them, and no code changed — only prose. I retitled the PR to match its wider scope.

The same pull request, now +6/−5 across two commits, retitled *Fix the
line-count claims for codes.py and webhook.py*. It was merged; the numbers
you read in this repository's READMEs are the ones it fixed.

### What went wrong on the way

One thing: after the resumed pass the thread's `session:` label disappeared.
Adding a label and removing the same label in one `update_thread` call removes
it, and on a resume the new id is the old id. The agent now removes only
labels for *other* sessions. Not exercised: a third message on the thread
after that fix, `webhook.py` against a live delivery (its admission logic is
the tested `create_email_router`), and a task that trips the hook in a live run — the guard itself is covered
by `tests/test_coding_guard.py`, eighteen commands in and out.

## Adapting it

- `ALLOWED_REPOS` is the blast radius. One repository is a good start.
- The system prompt says "make the change the task asks for, and no more"
  and "if the task is ambiguous, stop and ask". Both held in the run above;
  keep them.
- `MAX_TURNS` (default 60) is the other budget. A task that cannot finish in
  sixty turns is a task to split.
