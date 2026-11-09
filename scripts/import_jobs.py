#!/usr/bin/env python3
"""Replace data/jobs.json with the approved jobs exported from the review page.

Usage: python3 scripts/import_jobs.py <folder-with-json-files>

The folder holds one JSON file per approved job (the review page's "jobs"
collection, saved with ArtifactData `out_dir`). The file name without .json
is the job id. The review page is the source of truth: a job that is no
longer there (taken down) disappears from the site too.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIELDS = [
    "title", "company", "location", "province", "field", "employment_type",
    "degree", "deadline", "posted", "summary", "requirements", "apply_url",
    "approved_at",
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    src = pathlib.Path(sys.argv[1])
    files = sorted(src.rglob("*.json"))
    jobs = []
    for f in files:
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"skip {f.name}: {e}")
            continue
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        job_id = re.sub(r"[^a-z0-9-]", "-", f.stem.lower()).strip("-")
        url = str(data.get("apply_url", ""))
        if not job_id or not url.startswith(("http://", "https://")):
            print(f"skip {f.name}: missing id or apply_url")
            continue
        job = {"id": job_id}
        for k in FIELDS:
            v = data.get(k, "")
            job[k] = v if isinstance(v, str) else str(v)
        jobs.append(job)

    jobs.sort(key=lambda j: j.get("approved_at", ""), reverse=True)
    out = ROOT / "data" / "jobs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    new = json.dumps(jobs, ensure_ascii=False, indent=2) + "\n"
    old = out.read_text(encoding="utf-8") if out.exists() else ""
    out.write_text(new, encoding="utf-8")
    print(f"{len(jobs)} jobs written to data/jobs.json ({'changed' if new != old else 'unchanged'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
