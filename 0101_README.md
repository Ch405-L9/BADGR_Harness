# BADGR Harness — Conditional Context + Retrieval Architecture Evaluation

## Objective

Evaluate and refine the BADGR Harness so that task classification remains lightweight while **BM25 and/or ChromaDB retrieval performs the heavy contextual retrieval work**.

Do not redesign the entire harness. Work from the existing architecture and identify the smallest correct change.

## Current Known State

The harness currently has two classification mechanisms:

1. **Simple keyword router:** **7/7 PASS**
2. **AI classifier (`llama3.2:3b`):** **6/7 PASS**

The AI classifier is currently over-classifying the three real evaluation tasks as:

```text
GPU / VRAM question → planning
Finance / math question → planning
Competitive business strategy → planning
```

Therefore:

```text
USER
→ AI CLASSIFIER
→ WRONG `planning` LABEL
→ WRONG DOWNSTREAM PATH
→ BAD RESULT
```

The keyword router itself is not currently the primary problem.

We have **not yet proven** whether forcing/bypassing the classifier produces a correct downstream answer. That must remain a separate experiment.

---

## Context Selection Requirement

The harness must **NOT blindly inject entire files, entire directories, or the entire repository into the model context.**

For each task:

### Required

Retrieve only:

1. The **minimum relevant context** from the two primary directive/context files.
2. Any additional file **only if it is conditionally relevant** to the current task.
3. The relevant retrieved passages rather than entire unrelated files.

Think:

```text
CURRENT USER TASK
        ↓
TASK UNDERSTANDING
        ↓
RELEVANCE FILTER
        ↓
BM25 / ChromaDB
        ↓
ONLY RELEVANT CONTEXT
        ↓
MODEL
```

Not:

```text
CURRENT USER TASK
        ↓
DUMP ENTIRE REPOSITORY
        ↓
MODEL
```

---

## Retrieval Responsibility

Determine whether **BM25, ChromaDB, or a hybrid of both** should perform the retrieval workload.

Expected conceptual division:

### BM25

Use for:

- exact terminology
- lexical matches
- filenames
- identifiers
- technical terms
- explicit phrases
- deterministic keyword relevance

### ChromaDB / vector retrieval

Use for:

- semantic similarity
- concepts expressed using different wording
- related instructions
- contextual meaning
- concept-level retrieval

### Hybrid

If both are already available, evaluate whether the best architecture is:

```text
BM25 + ChromaDB
       ↓
candidate retrieval
       ↓
relevance filtering/ranking
       ↓
small context package
       ↓
LLM
```

Do not assume either technology is automatically superior. Verify against the existing implementation.

---

## Conditional File Inclusion

The two primary directive/context files should be treated as the **base authoritative context**.

Everything else should be conditional.

A file should enter the model context only when:

```text
RELEVANT TO CURRENT TASK = TRUE
```

Otherwise:

```text
INCLUDE = FALSE
```

Examples:

```text
GPU / VRAM task
→ retrieve GPU/model/runtime material
→ do not retrieve finance, marketing, MCP, or unrelated project material

Finance calculation
→ retrieve relevant business/pricing/financial material
→ do not retrieve GPU or unrelated engineering material

Business strategy
→ retrieve relevant strategy/business material
→ do not retrieve unrelated code/runtime material

MCP task
→ retrieve MCP-specific material
→ do not automatically inject every RAG or repository document
```

---

## Important Separation of Concerns

Keep these failure classes separate:

### 1. Classification Failure

```text
Correct task
→ wrong task_type
```

Current observed issue:

```text
GPU → planning
Math → planning
Strategy → planning
```

### 2. Retrieval Failure

```text
Correct task_type
→ wrong / missing context retrieved
```

### 3. Generation Failure

```text
Correct task_type
→ correct context
→ incorrect model answer
```

### 4. Grounding Failure

```text
Model answer contains claims
→ claims unsupported by retrieved context
```

Do not report one failure as another.

---

## Current Known Evaluation Evidence

### Deterministic Router

```text
research        → research        PASS
classification  → classification  PASS
code            → code            PASS
extraction      → extraction      PASS
summarization   → summarization   PASS
planning        → planning        PASS
general         → general         PASS
```

Result:

```text
7/7 PASS
```

### AI Classifier

Using `llama3.2:3b`:

```text
research        → research        PASS
classification  → classification  PASS
code            → code            PASS
extraction      → extraction      PASS
summarization   → summarization   PASS
planning        → planning        PASS
general         → extraction      FAIL
```

Result:

```text
6/7 PASS
```

### Real Evaluation Tasks

```text
GPU / VRAM      → planning
Finance / math  → planning
Business        → planning
```

These results indicate classifier/routing behavior requires investigation.

The finance test also produced incorrect arithmetic, but **do not automatically attribute that arithmetic failure to classification** until a downstream bypass/controlled comparison proves causality.

---

## Evaluation Order

Use a strict A/B loop.

### A

Test current behavior.

### B

Change **one variable only**.

### PASS

Keep the change.

### FAIL

Revert/diagnose and test the next isolated variable.

Do not simultaneously change:

- classifier
- prompts
- RAG
- BM25
- ChromaDB
- MCP
- model
- dataset

because that destroys causal evidence.

---

## Required Architecture Question

Determine from the existing repository:

> What is the smallest architecture in which task classification identifies the broad task class, while BM25/ChromaDB conditionally retrieves only the context required for that task?

The desired model behavior is:

```text
CLASSIFIER = WHAT KIND OF TASK IS THIS?
RETRIEVAL  = WHAT INFORMATION DO I NEED?
LLM        = USE THAT INFORMATION TO PRODUCE THE ANSWER
```

The classifier should **not become the repository's knowledge engine**.

The retrieval layer should carry the contextual burden.

---

## Additional Things That Must Be Verified

Before modifying implementation, inspect the existing repository for:

- the two primary directive/context files
- existing RAG implementation
- existing BM25 implementation
- existing ChromaDB/vector implementation
- current document/chunk metadata
- current retrieval filters
- current context assembly
- current prompt construction
- current MCP configuration
- whether retrieval happens before or after classification
- whether retrieved context is actually passed to the final model
- whether irrelevant files can currently leak into context
- whether task type controls retrieval scope
- whether retrieval results can be logged for evaluation
- whether the exact retrieved chunks can be reproduced

Do **not** assume a component is functional merely because a file/configuration exists.

---

## Success Condition

The architecture should eventually demonstrate:

```text
TASK
 ↓
LIGHTWEIGHT CLASSIFICATION
 ↓
CONDITIONAL RETRIEVAL
 ↓
BM25 / CHROMA
 ↓
SMALL RELEVANT CONTEXT
 ↓
MODEL
 ↓
VALIDATED ANSWER
```

with measurable evidence for:

```text
classification = correct
retrieval = relevant
context = minimal
answer = correct
grounding = supported
```

The immediate next objective remains:

**isolate and correct the classifier/routing problem before expanding RAG/BM25/ChromaDB/MCP.**