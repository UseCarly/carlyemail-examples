# Your framework, wired to an inbox

The smallest useful email agent, once per framework. It reads what arrived,
answers what it can from the thread, and writes a draft — instead of sending
— when the request needs a commitment it cannot verify.

| Variant | Framework | Model auth |
|---|---|---|
| [`openai/`](openai) | OpenAI Agents SDK | `OPENAI_API_KEY` |
| [`langchain/`](langchain) | LangChain + LangGraph | `OPENAI_API_KEY` |
| [`claude/`](claude) | Claude Agent SDK | `ANTHROPIC_API_KEY` |

All three connect to the hosted MCP server, so there are no tool wrappers
to write.

```bash
cd openai        # or langchain, or claude
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # one pass
uvicorn webhook:app --port 8080   # or: run when mail arrives
```
