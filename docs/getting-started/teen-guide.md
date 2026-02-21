# Teen Guide (Beginner Friendly)

If you know basic Python, you can run everything here.

## Think of SuperCodeMode Like This

You have a robot assistant with two powers:

- `search` style tool to understand what is available
- `execute` style tool to run code and produce results

The robot often makes bad choices. SuperCodeMode trains the robot text instructions so it chooses better.

## Simple Mental Model

1. Give a question.
2. Robot picks a tool.
3. We score if answer is good.
4. GEPA updates text instructions.
5. Repeat with small budget.

## Start in 3 Commands

```bash
pip install -e .
scm doctor
scm showcase --runner mcp-http
```

This Cloudflare mode uses `https://mcp.cloudflare.com/mcp` by default.

## Want Safer Execution

Use Docker backend:

```bash
python examples/showcase_mcp_stdio.py --executor-backend docker
```

## Want Real LLM Optimization

```bash
export GOOGLE_API_KEY=your_key_here
python examples/optimize_gemini_flash.py --max-metric-calls 4
```

## Where to Look Next

- Examples page for all runnable scripts
- GEPA Adapter Changes page to understand what is optimized
- Code Map page to understand each file
- Troubleshooting page if something fails
