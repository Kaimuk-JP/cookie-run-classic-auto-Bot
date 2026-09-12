import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

MACROS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "macros"
)


def ensure_macros_dir():
    """Ensure the macros directory exists."""
    os.makedirs(MACROS_DIR, exist_ok=True)


def list_macros() -> List[Dict[str, Any]]:
    """List all available macro profiles with metadata summary."""
    ensure_macros_dir()
    macros = []
    for fname in os.listdir(MACROS_DIR):
        if not fname.endswith(".json"):
            continue
        filepath = os.path.join(MACROS_DIR, fname)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                macros.append(
                    {
                        "id": data.get("id", os.path.splitext(fname)[0]),
                        "name": data.get("name", fname),
                        "description": data.get("description", ""),
                        "author": data.get("author", "Unknown"),
                        "created_at": data.get("created_at", ""),
                        "duration_seconds": data.get("duration_seconds", 0.0),
                        "loop": data.get("loop", False),
                        "action_count": len(data.get("actions", [])),
                        "filename": fname,
                    }
                )
        except Exception:
            pass
    macros.sort(key=lambda x: x["name"])
    return macros


def get_macro(macro_id: str) -> Optional[Dict[str, Any]]:
    """Load and return complete macro data by ID."""
    ensure_macros_dir()
    clean_id = os.path.basename(macro_id).replace(".json", "")
    filepath = os.path.join(MACROS_DIR, f"{clean_id}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_macro(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate and save macro profile."""
    ensure_macros_dir()
    if not isinstance(data, dict):
        return False, "Invalid macro payload (must be JSON object)"

    macro_id = str(data.get("id", "")).strip()
    if not macro_id:
        macro_name = str(data.get("name", "macro")).strip()
        macro_id = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in macro_name
        ).lower()
        if not macro_id:
            macro_id = f"macro_{int(time.time())}"
        data["id"] = macro_id

    # Clean filename
    clean_id = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in macro_id
    ).lower()
    data["id"] = clean_id

    # Ensure actions list is sorted by timestamp
    actions = data.get("actions", [])
    if isinstance(actions, list):
        for act in actions:
            if "t" in act:
                try:
                    act["t"] = round(float(act["t"]), 3)
                except Exception:
                    act["t"] = 0.0
        actions.sort(key=lambda x: x.get("t", 0.0))
        data["actions"] = actions

        # Calculate max duration
        if actions:
            last_t = actions[-1].get("t", 0.0)
            data["duration_seconds"] = max(
                float(data.get("duration_seconds", 0.0)), last_t + 2.0
            )

    filepath = os.path.join(MACROS_DIR, f"{clean_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, clean_id
    except Exception as e:
        return False, str(e)


def delete_macro(macro_id: str) -> bool:
    """Delete a macro profile file."""
    ensure_macros_dir()
    clean_id = os.path.basename(macro_id).replace(".json", "")
    filepath = os.path.join(MACROS_DIR, f"{clean_id}.json")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception:
            return False
    return False
