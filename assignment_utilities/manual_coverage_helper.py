from __future__ import annotations

from typing import Dict, List


COV: Dict[str, List[bool]] = {}


def init_function(func_name: str, slots: int = 100) -> None:
    """
    Initialise a fixed-size branch coverage array for a function.
    Call this once at the start of the test run.
    """
    COV[func_name] = [False] * slots


def hit(func_name: str, branch_id: int) -> None:
    """
    Mark a particular branch as taken.
    """
    try:
        COV[func_name][branch_id] = True
    except KeyError as exc:
        raise RuntimeError(
            f"Coverage for function '{func_name}' was not initialised. "
            f"Call init_function('{func_name}') before running."
        ) from exc
    except IndexError as exc:
        raise RuntimeError(
            f"Branch id {branch_id} is out of range for function '{func_name}'."
        ) from exc


def report(*, only_hit: bool = True) -> str:
    """
    Return a human-readable report string. Print it or write it to a file.
    """
    lines: list[str] = []
    for func_name, flags in sorted(COV.items()):
        taken = sum(1 for f in flags if f)
        total = len(flags)
        lines.append(f"{func_name}: {taken}/{total} ≈ {round(taken/total, 2)*100}% branch coverage")
        if only_hit:
            hits = [i for i, f in enumerate(flags) if f]
            lines.append(f"  hit IDs: {hits}")
        else:
            lines.append(f"  flags: {flags}")
    return "\n".join(lines)
