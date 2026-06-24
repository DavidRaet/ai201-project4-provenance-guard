# Provenance Guard - planning.md

## Project Overview

Provenance Guard is a backend classification system that analyzes submitted creative text and determines whether it is likely AI-generated or human-authored. It returns a structured attribution result, confidence score, and a plain-language transparency label. Creators can appeal classifications, and all decisions are recorded in a structured audit log.

**Stack:** Flask · Groq (llama-3.3-70b-versatile) · Stylometric heuristics (pure Python) · Flask-Limiter · SQLite / structured JSON (Will be decided)

***

## Rate Limiting

### Strategy

Rate limiting is applied per **IP address** using Flask-Limiter's default `get_remote_address` key function. Since Provenance Guard has no authentication layer in v1, there are no user accounts to key on and IP is the practical next best option. The trade-off is that users behind shared NATs could be unfairly grouped under one limit, but for a small-scale academic project, this is an acceptable simplification.

The algorithm used is Flask-Limiter's default **fixed window**. Essentially when a certain limit is applied, the library creates a counter keyed to the client's IP address and the specific endpoint.

### Chosen Limits

| Endpoint | Limit | Window | Reasoning |
|---|---|---|---|
| `POST /submit` | **10 requests** | per minute | The classification pipeline calls Groq. Each call has latency and counts against Groq's free-tier rate limit. 10/min gives a real user room to test their integration without hammering the LLM. A malicious scan would burn through 10 quickly and get a 429. |
| `POST /appeal` | **5 requests** | per minute | Appeals are low-frequency by design. A creator disputing a decision does not need to submit more than 5 appeals in 60 seconds. This limit prevents log pollution from duplicate or bulk submissions. |
| `GET /log` | **30 requests** | per minute | Read-only, no external calls. 30/min is generous enough for interactive debugging without opening a trivial DoS vector on the log file. |

### What Happens When the Limit Is Hit

Flask-Limiter returns a `429 Too Many Requests` response automatically. The response body will include a message like:

```json
{
  "error": "Rate limit exceeded. Try again in 60 seconds.",
  "status": 429
}
```

A `Retry-After` header will be included so the client knows exactly when to retry [1].

***

### Strategy

### Chosen Limits

***

## Detection Signals

### Signal Combination

***

## Transparency Label Variants

***

## Appeals Workflow

### Workflow Steps


### Anticipated Edge Cases


***


## Architecture

***

## AI Tool Plan


### M3 - Submission Endpoint + First Signal (LLM)

**When:** 



**What I will ask the AI to generate:**

**How I will verify the output:**

***

### M4 - Second Signal + Full Confidence Scoring

**When:** After M3 passes manual testing.

**Spec sections provided as input:**

**What I will ask the AI to generate:**


**What I will check:**

***

### M5 - Production Layer (Labels, Appeals, Audit Log)

**When:** 

**Spec sections provided as input:**


**What I will ask the AI to generate:**


**How I will verify:**

***

## Endpoint Summary

***