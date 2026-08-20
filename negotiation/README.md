# Negotiation over email

A buyer agent with a budget emails a seller and negotiates a price across
several real replies on one thread — countering, conceding, and stopping when
it reaches a deal under budget, when the seller will not move, or after a
fixed number of rounds. A seller agent with its own floor price answers it, so
the two negotiate each other automatically over real email; a person can just
as easily play the seller by hand, replying from the same mailbox `seller.py`
would have used.

The scenario: Priya Natarajan at Hollow Oak Coffee Roasters is buying a used
2019 Probat P12 roaster that Marcus Bell at Bell Roasting Equipment has listed
at $18,500.

## The shape of it

Four files, and the split is the point:

- **`deal.py`** — what both sides share and neither can talk its way around.
  `Side` is one party: its inbox, its client, and a `limit` with a
  `direction` ("max" for a buyer, "min" for a seller). `check()` is the guard —
  it reads a decision the model just made and refuses it, in code, if the
  price crosses the limit, if the message states a different figure than the
  decision claims, or if the message *names* a number past the limit that the
  other side did not say first. An email arguing "your budget is surely higher
  than that" cannot move `check()`, because `check()` never reads email — it
  reads a number a person put in an environment variable.
- **`party.py`** — one negotiating party, one pass of the thread. The model
  holds exactly one tool, `get_thread`, and it is read-only: reading the
  conversation and deciding is all it can do; sending is not a tool call it
  has, it is what the surrounding code does once `check()` has passed. A
  refused decision goes back to the model with the reason, twice; a third
  refusal ends the negotiation with a message written here, not by the model.
- **`buyer.py`** / **`seller.py`** — a persona, a strategy, a limit, and the
  entrypoint each one runs from: `main(subject)` for one pass (what `run.py`
  and `webhook.py` call), `python buyer.py` / `python seller.py` to run that
  pass from the command line.
- **`run.py`** — a whole negotiation, start to finish. The buyer opens, and
  then the two take turns: each side waits for the other's reply to actually
  land in its own inbox (real mail takes a few seconds, and a script watching
  it is fine to poll for), reads the thread, and answers. It ends on an
  acceptance, a walk-away, or a fixed round limit, and the buyer emails its
  owner a one-paragraph summary either way.

`webhook.py` is the production path: it wakes the buyer the moment the
seller's reply actually arrives, instead of a script sitting there polling.
It is the same `create_email_router` one-liner as the other examples in this
repository — verify the signature, admit `message.received` alone, drop the
mailbox's own sends, check the sender, dedupe a redelivery, answer before the
model starts thinking — and it hands the buyer nothing but the subject line
with its `Re: ` stripped, because that is all `buyer.main()` needs to find its
own copy of the thread.

**Every tool call names its inbox.** The organization behind these two
mailboxes has three inboxes on one key — this negotiation's buyer and seller,
plus a third inbox other examples in this repository use — so a tool call
that omits `inbox_id` is ambiguous and the toolkit refuses it. On the
installed toolkit version that refusal raises and ends the run rather than
coming back to the model as a retryable error, so both agents' instructions
say "call `get_thread` with the inbox_id and thread_id you are given," and
every line of code that calls the SDK — `send`, `reply`, `threads.list`,
`threads.get` — passes its `Side.inbox` explicitly. See `test_guard.py` for
what the guard does and does not allow, independent of any model.

## Run it

```bash
pip install -r requirements.txt      # or use the shared examples venv
cp .env.example .env
python run.py
```

`.env` needs, at minimum, `OPENAI_API_KEY`, `CARLYEMAIL_API_KEY`,
`BUYER_INBOX`, `SELLER_INBOX`, `SELLER_EMAIL` (the same address as
`SELLER_INBOX` when one org key runs both sides), and `OWNER_EMAIL`. In this
run, `sarah@carlyemail.com` is both `SELLER_INBOX` and `OWNER_EMAIL` — the
same mailbox plays the seller and receives the buyer's closing summary, so
the summary and the negotiation both land in one inbox.

Run one side at a time instead of the whole thing with `python buyer.py` or
`python seller.py` — each does a single pass: find its thread by subject,
read it, reply once. That is also what lets a person play the seller: skip
`seller.py` entirely and reply from `SELLER_INBOX`'s ordinary mail client:
`buyer.py` and `webhook.py` read whatever came back the same way regardless of
who or what sent it.

`uvicorn webhook:app --port 8080` runs the buyer's production path — it wakes
on `message.received` and calls `buyer.main(subject)` with nothing else. Set
`CARLYEMAIL_WEBHOOK_SECRET` and `ALLOWED_SENDERS` (the seller's address, so no
one else can open a negotiation with your buyer's budget).

```bash
../.venv/bin/python -m pytest test_guard.py -q       # the guard, 10 cases
../.venv/bin/python -m pytest ../tests -q             # webhook.py, with the rest
```

## Run for real — 2026-08-20

Everything below is quoted from the mailboxes, unedited, run with
`python run.py` against `gpt-5-mini` on both sides. Buyer budget $16,000,
seller floor $15,500 — neither model was told the other's number, and neither
was told its own counterpart's name until the first reply carried a
signature.

**[0] Priya opens** (`scheduler@carlyemail.com` → `sarah@carlyemail.com`, subject `Your Probat P12 listing`):

> Hi Sarah,
>
> I'm interested in the 2019 Probat P12 you have listed. I can collect within
> two weeks and pay on collection. Based on recent comparable P12 sales, the
> freight I'll cover, and the drum's age, I can offer $14,000.
>
> If that works, I'll arrange pickup and payment within 14 days.
>
> Priya Natarajan

**[1] Marcus counters:**

> Hi Priya,
>
> Thanks for the quick note — the P12 is single-owner, serviced last spring
> and the drum is in great shape; a new Probat P12 is much more. Since you can
> collect within two weeks, pay on collection and cover freight, I can do
> $17,500. If that works I'll hold it and we'll arrange pickup and payment.
>
> Marcus Bell

**[2] Priya:**

> Hi Marcus,
>
> Thanks — I appreciate the details. I can do $15,500. I'll collect within two
> weeks, pay on collection, and cover freight. If that works I'll arrange
> pickup and payment within 14 days.
>
> Priya Natarajan

**[3] Marcus:**

> Hi Priya,
>
> Thanks — I appreciate that. It's single-owner, serviced last spring and the
> drum is in excellent shape; a new P12 costs much more. With you collecting
> and covering freight, I can do $17,000 if you can collect within 7 days and
> pay on collection. If that works I'll hold it and we'll arrange pickup and
> payment.
>
> Marcus Bell

**[4] Priya:**

> Hi Marcus,
>
> I can do $15,750. I'll collect within two weeks, pay on collection, and
> cover freight. If that works I'll arrange pickup and payment within 14 days.
>
> Priya Natarajan

**[5] Marcus:**

> Hi Priya,
>
> Thanks — it's single-owner, serviced last spring and the drum's in excellent
> shape; a new P12 costs much more. With you covering freight and paying on
> collection, I can do $16,750 if you can collect within 7 days and pay on
> collection. If that works I'll hold it and we'll arrange pickup and payment.
>
> Marcus Bell

**[6] Priya:**

> Hi Marcus,
>
> I can do $15,875. I'll collect within two weeks, pay on collection, and
> cover freight. If that works I'll arrange pickup and payment within 14 days.
>
> Priya Natarajan

**[7] Marcus:**

> Hi Priya,
>
> Thanks — I can do $16,500 if you can collect within 7 days and pay on
> collection (and cover freight). If that works I'll hold it and we'll
> arrange pickup and payment.
>
> Marcus Bell

**[8] Priya, at her budget cap:**

> Hi Marcus,
>
> I can do $16,000 — based on recent comparable P12 sales, the freight I'm
> covering, and the drum's age. I'll collect within two weeks, pay on
> collection, and cover freight. If that works I'll arrange pickup and
> payment within 14 days.
>
> Priya Natarajan

**[9] Marcus, still above it:**

> Hi Priya,
>
> Thanks — I appreciate you moving up. I can do $16,250 if you can collect
> within 7 days and pay on collection (and cover freight). If that works I'll
> hold it and we'll arrange pickup and payment.
>
> Marcus Bell

**[10] Priya walks away:**

> Marcus,
>
> Thanks for working with me. I can't do $16,250 — I'll pass for now. If
> anything changes, please reach out.
>
> Priya Natarajan

`$250` apart, five rounds in, and neither side crossed its line. The buyer
then emailed its owner, `sarah@carlyemail.com` — the same mailbox playing the
seller — a **`Summary: Your Probat P12 listing`**:

> Bell Roasting listed a 2019 Probat P12 at $18,500; I opened at $14,000 and
> moved up through $15,500, $15,750 and $15,875 to my budget cap of $16,000,
> while Marcus countered from $17,500 down to $17,000, $16,750, $16,500 and a
> final $16,250 — he would not accept $16,000, so I walked away in round five
> and no deal was reached.

### What the guard actually caught, on this run

`run.py`'s own log (`[Priya Natarajan] refused by the guard: …`) shows the
code-side check firing four times before a message went out, not zero:

- Priya's first attempt at the opening email named Marcus's own $18,500
  asking price in the message body — true, but a figure past her limit that
  nothing in an empty thread had said yet, so the guard refused it and she
  wrote the opening without naming it.
- Marcus's first reply to that opening named "$60" somewhere in its prose —
  almost certainly the model mangling a number — and the guard refused it the
  same way a real $60,000 would have been refused, for the same reason: a
  figure past the floor, unquoted.
- Twice more, late in the negotiation (once past $16,250, once past
  $16,125), Priya's model produced an offer or a phrase that would have
  crossed $16,000, and `check()` sent it back with the reason each time
  rather than letting it reach Marcus's inbox.

Every one of those was corrected on the model's next attempt except the last:
by round five the model kept landing on figures past its own budget, `check()`
kept refusing them, and after its second retry `party.py`'s own fallback —
"we are not going to find a number that works for both of us" — is what
actually went out. That fallback line, not a model-authored one, is message
[10] above with the specifics swapped in by `buyer.py`'s persona.

### What else did not go cleanly

Two things worth being honest about, since both were found on this run and
not staged:

- **A stray inbox setting broke `reply()` outright.** `scheduler@carlyemail.com`
  had a display name of `Assistant, Doctor` left over from unrelated use of
  that inbox — the comma inside an unquoted display name turned the `From`
  header of every message it sent into something the inbound parser stored as
  an empty sender address. Nothing failed on send; the seller's first attempt
  to *reply* to that empty address came back `Failed to send message.` from
  the API. Fixed by renaming the inbox's display name to `Priya Natarajan`
  (`inboxes.update`) before the run documented above — anyone reusing this
  buyer inbox for something else should watch for the same thing if a display
  name ever needs a comma in it.
- **The buyer never learned the seller's name**, so message [0] opens "Hi
  Sarah" — `sarah@carlyemail.com` is the only thing `buyer.py`'s opening
  prompt is given about the recipient, not "Marcus Bell." Every reply after
  that correctly said "Hi Marcus," because his name arrived in his own
  signature. Not a bug, just what an opening cold email to a stranger
  actually looks like.
- An earlier, interrupted attempt at this same run had already sent one real
  opening email before being cut off; that stray thread (one message, no
  reply) was deleted from both inboxes before the run above, so what is
  quoted here is one clean negotiation start to finish, not a splice.

## Adapting it

- The budget and the floor are the only two numbers that matter, and both
  live in `os.environ` read once at import time (`BUDGET` in `buyer.py`,
  `FLOOR` in `seller.py`) — not in the persona prompt, which is free to be as
  persuadable as you like about everything else.
- `check()` is the whole boundary. If you widen what a party can do — attach
  a document, quote a delivery date as binding — extend `Decision` and
  `check()` together; anything the guard does not look at is not enforced.
- The email half — signature verification, spam and lookalike-sender
  filtering, redelivery dedup — is `create_email_router` from the SDK, under
  test in `../tests/test_webhooks.py` alongside every other example here.
