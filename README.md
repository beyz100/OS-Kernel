# OS Kernel Simulation Project

A preemptive OS kernel simulator implementing core subsystems:
**process scheduling** (FIFO & Round-Robin), **paged memory management** with clock (second-chance) replacement, **mutex/CV synchronization** with deadlock detection, and a **cached file system** with disk-quota enforcement.

## Requirements

- Python **3.10 or newer** (the codebase uses PEP 604 / PEP 585 type-hint syntax such as `int | None` and `dict[int, list[int]]`, which is invalid on 3.9 and earlier).

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
python main.py
```

## Tests

```bash
pytest tests/ -v
```

## Project Structure

| Directory | Description |
|-----------|-------------|
| `core/`   | Kernel subsystems — scheduler, memory manager, sync primitives, file system, deadlock detector |
| `tests/`  | Unit tests for each subsystem |
| `utils/`  | Logger and clock utility |
| `main.py` | All simulation scenarios (baseline, cross-component, failure, stress) |