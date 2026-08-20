# The smallest email agent, on your framework

It reads what arrived, answers what it can, and saves a draft instead of
sending when the answer needs a person — like approving a refund.

| | Framework | Key |
|---|---|---|
| [`openai/`](openai) | OpenAI Agents SDK | `OPENAI_API_KEY` |
| [`langchain/`](langchain) | LangChain | `OPENAI_API_KEY` |
| [`claude/`](claude) | Claude Agent SDK | `ANTHROPIC_API_KEY` |

All three connect over MCP. The email part is the same in each.

```bash
cd openai        # or langchain, or claude
pip install -r requirements.txt
cp .env.example .env
python agent.py                   # run once
uvicorn webhook:app --port 8080   # or run whenever mail arrives
```
