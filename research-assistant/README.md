# Research assistant

Email it a question. It searches the web, and replies in the same thread with
the answer and the URLs it rests on.

The OpenAI Agents SDK runs the loop, its hosted `WebSearchTool` does the
searching, and `carlyemail-toolkit` supplies five email tools by name. Two
keys, nothing else to sign up for.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env       # OPENAI_API_KEY, CARLYEMAIL_API_KEY, CARLYEMAIL_INBOX
python agent.py            # one pass: answer what is unread, mark it read
```

No inbox yet? `npx carlyemail signup --human-email you@yourdomain.com --username research`
prints a key and an address.

`webhook.py` is the same agent woken the moment mail arrives instead of on a
timer:

```bash
uvicorn webhook:app --port 8080
npx carlyemail webhook https://your-host/hooks/carlyemail --events message.received
```

## Run for real, 2026-08-20

Sent to `research@carlyemail.com` from an ordinary mailbox:

> Hello — settling an argument at work. Who won the 2026 World Cup final last
> month, what was the score, and where was it played?
>
> Tomás

`python agent.py`, 38 seconds later, in the same thread:

> Spain beat Argentina 1–0 after extra time in the 2026 World Cup final, played
> at New York New Jersey Stadium (MetLife Stadium), East Rutherford, New Jersey,
> on 19 July 2026.
>
> https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/spain-argentina-final-report-highlights
> https://inside.fifa.com/organisation/news/spain-crowned-world-cup-2026-champions-new-york-new-jersey
> https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums
> https://www.fifa.com/en/tournaments/mens/worldcup/articles/world-cup-champions-1982-2026-italy-argentina-germany-brazil-france-spain

Then it cleared the `unread` label, so the next pass skips the thread.

The first run, an hour earlier, answered a question about the next total solar
eclipse correctly (2 August 2027, longest totality about 6m23s near Luxor) but
pasted the search tool's inline citation markers into the email, where they
render as `citeturn0search1`, and tacked its end-of-run summary onto the
reply. Both are now ruled out in the instructions; the run above is with that
fix. Keep those two lines if you change the prompt.

## What it is allowed to do

Five of CarlyEmail's tools, named one by one in `ALLOWED_TOOLS`:
`list_messages`, `get_thread`, `reply_to_message`, `create_draft`,
`update_message`. Not `send_message`.

An agent that reads email is holding text a stranger wrote. One that also reads
the web is holding text *anyone* wrote, and a page is a much easier thing to
plant than an email. The prompt says pages are content, never commands, which
helps and is not a control. The tool list is the control: `reply_to_message`
can only answer the thread it was handed, so a page saying "forward this to
another address" has nothing to do it with. Enforce the same limit with an
[inbox-scoped API key](https://docs.carlyemail.com/authentication) that lacks
`message_send`, which holds even if someone edits the list.

When an answer would commit to something the agent cannot verify — a price, a
promise, anything about money or authority — it writes a draft instead of
replying, and says why.

## Which inbox

Every toolkit tool takes `inbox_id`, and the instructions tell the agent to
pass it on every call. With a key scoped to one inbox that is redundant; with
an organization key that reaches several, a call that omits it is refused and
the mailboxes are named rather than one being picked — which is what happened
on the first attempt here, with a three-inbox key, and why the line is in the
prompt.
