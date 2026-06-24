# Provenance Guard - planning.md

## Project Overview

Provenance Guard is a backend classification system that analyzes submitted creative text and determines whether it is likely AI-generated or human-authored. It returns a structured attribution result, confidence score, and a plain-language transparency label. Creators can appeal classifications, and all decisions are recorded in a structured audit log.

**Stack:** Flask · Groq (llama-3.3-70b-versatile) · Stylometric heuristics (pure Python) · Flask-Limiter · SQLite / structured JSON (Will be decided)

***

## Rate Limiting

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