import json
from pathlib import Path
p = Path(r"F:\test\2026-07-24-08-21-57\assets\strategy_registry.json")
r = json.loads(p.read_text(encoding="utf-8"))
for s in r.get("strategies", []):
    note = s.get("note", "")
    # Only normalize duplicate V3 note tags; do not alter audit history or tested records.
    while " | V3(轮17,6策略栈): NECESSARY, Δ_minus_full=" in note:
        start = note.find(" | V3(轮17,6策略栈): NECESSARY, Δ_minus_full=")
        end = note.find(" | ", start + 3)
        if end < 0:
            end = len(note)
        tag = note[start:end]
        if note.count(tag) <= 1:
            break
        note = note.replace(tag + tag, tag)
        # Fallback for a separator between duplicate tags.
        note = note.replace(tag + " | " + tag, tag)
    s["note"] = note
p.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
r2 = json.loads(p.read_text(encoding="utf-8"))
print("registry JSON OK")
for s in r2.get("strategies", []):
    print(s["id"], "audit", len(s.get("audit", [])), "v3_note_occurrences", s.get("note", "").count("V3(轮17,6策略栈)"))
