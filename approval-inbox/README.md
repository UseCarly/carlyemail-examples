# Approval inbox

An inbox where nothing leaves until a person says so — and the person says so
by email.

Someone writes in. The agent reads the thread and writes its answer as a
**draft**, then emails the draft to an approver: the original message, the
proposed reply, one line of instructions. The approver replies `send` and the
draft goes out to the customer, on the customer's own thread. Reply with
anything else — "shorter, and say Thursday" — and the agent revises the draft
and asks again.

No dashboard, no queue to log in to. The approver does the whole job from
whatever they read mail in, including a phone.

## Run it

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
export CARLYEMAIL_API_KEY=ce_us_...
export CARLYEMAIL_INBOX=approvals@carlyemail.com
export APPROVER=you@yourcompany.com
export ABOUT="You are the shipping desk at Harbor Lane Furniture."
python agent.py
```

`agent.py` is one pass over the inbox: new mail gets drafted and sent for
approval, verdicts get acted on. `webhook.py` runs the same pass whenever mail
arrives — a request or a verdict, the same way:

```bash
uvicorn webhook:app --port 8080
```

`ALLOWED_SENDERS` must include the approver, or their `send` never reaches the
agent.

## The two decisions that are never the model's

Whether a message **is** an approval — it came from `APPROVER` and carries the
draft id we put in the subject — and whether it says **send**, are both decided
in code. The model writes prose; it is never asked whether prose should leave
the building. `send` means exactly `send`: "send it, but shorter" is feedback,
because the safe reading of ambiguity is "not yet".

The model also never touches an id. It reads the thread with `get_thread` —
its only tool — and returns the body of a reply; code creates the draft
against the exact message it answers. The first version let the model call
`create_draft` itself, and on the first real run it dropped the closing `>`
from a Message-ID. Anything that has to be exact is done where exactness is
free.

The draft id rides in the approval email's subject (`[approve draft_…]`), so
the approver's reply brings it back through any mail client, a forward, or a
week later, with no state on this side to look it up in. Feedback on a draft
that was already sent gets a straight answer on the thread instead of a crash
— approvers do reply to old approval emails, and the first real run proved it.

## Run for real — 2026-08-20

Everything below is quoted from the mailboxes, unedited. `sarah@carlyemail.com`
plays both the customer and the approver; `approvals@carlyemail.com` is the
agent, running `gpt-5-mini`.

The customer writes in:

> **Subject: Can you gift-wrap order 7188?**
>
> Hi,
>
> Order 7188 (the walnut chess table) is a 60th birthday present for my dad.
> Could you gift-wrap it and leave the invoice out of the box? Delivery is
> booked for Saturday.
>
> Thanks,
> Sarah

`python agent.py` → `asked sarah@carlyemail.com to approve
draft_00mt1s9zsmxwus3e35jv4bwp`. The approver receives, under
**`[approve draft_00mt1s9zsmxwus3e35jv4bwp] Can you gift-wrap order 7188?`**,
the quoted request plus:

> Proposed reply to sarah@carlyemail.com:
>
> Hi Sarah,
>
> We can gift-wrap order 7188 (the walnut chess table) and will omit the
> invoice from the box. Delivery will remain scheduled for Saturday. We'll
> email the invoice to the address on the order.
>
> If you'd like a gift message included, please reply with the wording and how
> you'd like it signed.
>
> Thanks,
> Shipping Desk
> Harbor Lane Furniture
>
> Reply "send" and it goes. Reply with anything else and I will revise the
> draft and ask again.

The approver replies — not with `send`:

> Say yes to both, and mention the wrapping is free on orders over $200. Sign
> it Priya.

`python agent.py` → `revised draft_00mt1s9zsmxwus3e35jv4bwp and asked again`.
The revised proposal arrives on the same approval thread:

> Hi Sarah,
>
> Yes — we can gift-wrap order 7188 (the walnut chess table), and yes — we
> will omit the invoice from the box. Wrapping is free on orders over $200.
> Delivery will remain scheduled for Saturday. We'll email the invoice to the
> address on the order.
>
> If you'd like a gift message included, please reply with the wording and how
> you'd like it signed.
>
> Thanks,
> Priya

The approver replies `send`. `python agent.py` →
`sent draft_00mt1s9zsmxwus3e35jv4bwp as <00mt1saoechu5jgud6fs4q4x@carlyemail.com>`
— the customer receives exactly the approved text as
**`Re: Can you gift-wrap order 7188?`**, on their original thread, and the
approver gets one word back on theirs: `Sent.`

Two things the earlier, messier runs found, kept because they are the honest
part: the model mangling a Message-ID is what moved draft creation into code,
and an approver replying on a stale approval thread is what earned the
draft-already-sent reply instead of an exception.

## Adapting it

- The email half — signature verification, spam and lookalike-sender
  filtering, redelivery dedup — is `create_email_router` from the SDK, and is
  under test in `../tests/test_webhooks.py`.
- Hold the boundary with an [inbox-scoped API key](https://docs.carlyemail.com/authentication):
  this agent needs `message_read`, `message_send`, `draft_create`,
  `draft_update`, `draft_send`. Without `draft_send` on the key, even a bug in
  the `send` check could not send.
- Several approvers: check `address(message["from"])` against a set instead of
  one address. The token already carries everything else.
