"""Data-only routing environment. Reads are counted at the actual read boundary."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = {"implement": "PROGRAM.md", "prove": "PROVE.md", "diagnose": "diagnostics.json"}


def decode(raw):
    if len(raw) > 4096:
        raise ValueError("candidate exceeds 4096 bytes")
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("duplicate task")
            out[key] = value
        return out
    mapping = json.loads(raw, object_pairs_hook=pairs)
    if not isinstance(mapping, dict) or any(k not in TASKS or v not in TASKS.values()
                                            for k, v in mapping.items()):
        raise ValueError("routes must use declared task names and local pack filenames")
    return mapping


def resolve(task, routes, root=ROOT):
    if task not in TASKS:
        raise ValueError("task must be implement, prove, or diagnose")
    reads = []
    def read(file):
        reads.append(str(file))
        return file.read_bytes()
    mapping = decode(read(Path(routes)))
    if task not in mapping:
        # Fallback obtains the router before selecting the conventional pack.
        read(root / "guide/agent/ROUTER.md")
    at = root / "guide/agent" / mapping.get(task, TASKS[task])
    content = read(at)
    return {"task": task, "text": content.decode(), "reads": len(reads), "files": reads}
