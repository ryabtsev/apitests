# GenTests for Python

**Runtime test generation framework** 

Define `GenTestCase` blueprints with parameter sets; the framework generates a test for each combination, reducing boilerplate and increasing coverage.

## Key concepts

### AI-Powered Generation

Use a Large Language Model (e.g., Gemini) with a RAG system to auto-generate test parameters. The RAG fetches context from internal docs (API specs), and the LLM creates a dictionary of valid, invalid, and edge-case inputs for your `GenTestCase`.

### Black-Box Mocking

For black-box testing, `patch` your app's HTTP client to redirect traffic to a local **Active Stub Server**. The stub server queries the `GenTests` generator for dynamic, context-aware responses for each test, allowing you to test an unmodified application.

## Running the Generator

You can tag your `GenTestCase` tests and run them selectively with your test runner.

This will start test generation:

**Django:**
```bash
$ ./manage.py test animals --tag=generator
```

**Pytest:**
```bash
$ pytest tests/test_mod.py -m=generator
```




