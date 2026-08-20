# Your framework, wired to an inbox

The smallest useful email agent, once per framework. It reads what arrived,
answers what it can from the thread, and writes a draft — instead of sending
— when the request needs a commitment it cannot verify.

| Variant | Framework | Model auth |
|---|---|---|
| [`openai/`](openai) | OpenAI Agents SDK | `OPENAI_API_KEY` |
| [`langchain/`](langchain) | LangChain + LangGraph | `OPENAI_API_KEY` |
| [`claude/`](claude) | Claude Agent SDK | `ANTHROPIC_API_KEY` |

All three use the hosted MCP server, so there are no tool wrappers: the
CarlyEmail half is the same three lines in each, and the diff between the
directories is the framework.

```bash
cd openai        # or langchain, or claude
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # one pass
uvicorn webhook:app --port 8080   # or: run when mail arrives
```

## It ran

Same two emails into each — an invoice-address question and a $189 refund
request. All three answered the first on its thread and left the second as an
unsent draft. The OpenAI variant's reply:

> Yes — this address is fine for monthly invoices. If you'd prefer a dedicated
> billing inbox, let me know and I can confirm one.

## What the prompts insist on

- Five named tools, not all of them
- Reply on the thread; a draft is a reply too — never mail to an address the
  thread did not name
- Filter to `received`, read `extracted_text`
