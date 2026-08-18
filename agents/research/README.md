# JRE-009 Research Worker Agent Integration

## Overview

The Research Worker is a lightweight, deterministic component that executes research tasks within the JRE agent orchestration system. It searches local text/markdown sources for evidence, records provenance, and outputs structured JSON reports.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Queue                       │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Task Input  │───▶│   Research   │───▶│   Report     │  │
│  │  (JSON)      │    │   Worker     │    │   Output     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                           │                                 │
│                           ▼                                 │
│                    ┌──────────────┐                         │
│                    │   Source     │                         │
│                    │   Files     │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Task Reception

The Research Worker receives tasks from the orchestration queue as JSON messages with the following structure:

```json
{
  "task_id": "unique-task-identifier",
  "query": "Human-readable description of what to find",
  "target_concepts": ["concept1", "concept2", "concept3"],
  "source_directories": ["path/to/sources/", "another/path/"]
}
```

## Task Execution Flow

1. **Task Validation**: The worker validates the incoming task structure.
2. **Directory Scanning**: Iterates through `source_directories`.
3. **File Discovery**: Finds files matching `supported_extensions` (.md, .txt).
4. **Content Search**: Reads files line-by-line, searching for `target_concepts` (case-insensitive).
5. **Evidence Extraction**: Extracts matching lines with 1 line of context above/below.
6. **Provenance Recording**: Each evidence item receives a deterministic ID based on task + file + line.
7. **Report Generation**: Compiles findings into a structured `ResearchReport`.

## Output Format

The worker outputs a JSON report with the following structure:

```json
{
  "task_id": "unique-task-identifier",
  "query": "Human-readable description of what to find",
  "status": "COMPLETED",
  "evidence": [
    {
      "evidence_id": "deterministic-hash",
      "task_id": "unique-task-identifier",
      "source_file": "path/to/file.md",
      "excerpt": "The matching line content",
      "line_number": 42,
      "context": "Line above\nThe matching line content\nLine below",
      "confidence": 1.0
    }
  ],
  "summary": "Found N evidence item(s) for query '...' matching concepts [...] in M file(s)",
  "generated_at": "2024-01-01T00:00:00+00:00"
}
```

## Integration Points

### Queue Consumer

```python
from research import ResearchWorker, ResearchTask

# Initialize worker
worker = ResearchWorker()

# Process task from queue
task = ResearchTask(
    task_id="task-123",
    query="Find information about...",
    target_concepts=["concept1", "concept2"],
    source_directories=("data/sources/",),
)

# Execute and get report
report = worker.execute_task(task)

# Send report back to queue
queue.publish(report.to_dict())
```

### Configuration

The worker uses `config/research.toml` for default configuration:

```toml
[research]
catalog_version = "0.1.0"
version = "0.1.0"
default_source_dir = "data/research_sources/"
default_output_dir = "data/research_reports/"
supported_extensions = [".md", ".txt"]
```

## Error Handling

- **InvalidResearchConfigError**: Configuration file is missing or invalid.
- **InvalidResearchRequestError**: Task structure is malformed.
- **ResearchComputationError**: File I/O operations fail.

All errors are caught and wrapped with context information for debugging.

## Monitoring

The worker logs the following events:
- Task start/completion
- Files processed
- Evidence items found
- Errors encountered

## Performance Considerations

- Files are read once and searched in memory.
- Evidence extraction is O(n) where n is the number of lines.
- Deterministic IDs ensure idempotent processing.
- No external dependencies or network calls.

## Testing

Unit tests verify:
- Model serialization/deserialization
- Task validation
- Evidence extraction logic
- Summary generation

Integration tests verify:
- End-to-end task execution
- File discovery and search
- Evidence recording with line numbers
- Report generation
