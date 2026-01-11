# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the bt-mqtt project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## ADR Template

```markdown
# [Number]. [Title]

**Date:** YYYY-MM-DD

**Status:** [Proposed | Accepted | Deprecated | Superseded]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive

- Benefit 1
- Benefit 2

### Negative

- Drawback 1
- Drawback 2

### Neutral

- Side effect 1

## Alternatives Considered

What other options did we look at?
```

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./0001-python-scanner.md) | Python with Bleak for Scanner Agent | Accepted |
| [0002](./0002-typescript-subscriber.md) | TypeScript/Node.js for Subscriber | Accepted |
| [0003](./0003-mqtt-topic-structure.md) | MQTT Topic Naming Structure | Accepted |
| [0004](./0004-processing-pipeline.md) | Raw Capture vs Processing Split | Accepted |
| [0005](./0005-deduplication-strategy.md) | Time-Based Deduplication at Scanner | Accepted |
| [0006](./0006-parser-plugin-system.md) | Pluggable Parser Architecture | Accepted |
| [0007](./0007-scanner-id-manual-config.md) | Manual Scanner ID Configuration | Accepted |
| [0008](./0008-kysely-migrations.md) | Kysely for Type-Safe Queries and Migrations | Accepted |
| [0009](./0009-mqtt-failure-drop-messages.md) | Drop Messages on MQTT Failure | Accepted |
| [0010](./0010-parser-manual-registration.md) | Manual Parser Registration | Accepted |
