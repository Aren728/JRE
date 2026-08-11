# JRE Agent Orchestration

Agents communicate through versioned task specifications.

No agent may silently modify another subsystem.

Workflow:

REQUEST
  -> ARCHITECT
  -> SPECIALIST
  -> CODING
  -> QA
  -> VALIDATOR
  -> MERGE

The Architect controls dependencies and architectural decisions.
