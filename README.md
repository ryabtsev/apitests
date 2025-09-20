# APITESTS: AI-Powered Runtime Test Generator for Microservices

Define `GenTestCase` blueprints with parameter sets; the framework generates a test for each combination, reducing boilerplate and increasing coverage.

## Installation
```bash
$ pip install apitests
```

## Key concepts

### AI-Powered Generation

Use a Large Language Model (e.g., Gemini) with a RAG system to auto-generate test parameters. The RAG fetches context from internal docs (API specs), and the LLM creates a dictionary of valid, invalid, and edge-case inputs for your `GenTestCase`.

### Black-Box Mocking

For black-box testing, `patch` your app's HTTP client to redirect traffic to a local **Active Stub Server**. The stub server queries the `GenTests` generator for dynamic, context-aware responses for each test, allowing you to test an unmodified application.

### Data Collection During Generation and "live documentation"
As tests are generated and run, the framework can collect valuable data, such as:
-   Request/response payloads from mocked services.
-   Application logs emitted during the test.
-   Performance metrics like response times.

This data can be aggregated into a report, offering insights into the application's behavior under different scenarios and aiding in debugging. This collected data can then be fed into a corporate RAG system, creating a form of "live documentation" that reflects the application's actual, tested behavior.

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


## PYPI publising:
1. Fix version 

2. Build

```bash
$ python -m build
```

3. Upload to pypi
```bash
$ python -m twine upload dist/*
```

