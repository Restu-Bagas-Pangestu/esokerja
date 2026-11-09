# Esokerja

Static job-listing site for S-1 graduates in Indonesia, served by GitHub Pages from `docs/` on `main`.

- `data/jobs.json` — the approved jobs (source for the site). Never edit by hand during a sync; it is replaced from the review page.
- `build.py` — generates `docs/` (index, one page per job with JobPosting JSON-LD, about, privacy, sitemap, robots, 404). Standard library only.
- `src/style.css`, `src/app.js` — copied into `docs/assets/` by the build.
- `config.json` — site name, base URL/path. When a custom domain is bought: set `base_url` to `https://<domain>`, `base_path` to `/`, add `"custom_domain": "<domain>"`, rebuild.
- Site copy is in Indonesian.

## Review page (source of truth)

Approved jobs live in the review artifact's database: https://claude.ai/artifact/KKgy5qm1JDUwNWJfBoVSd1
collection `jobs` (approved, shown on the site) and `queue` (waiting for review — never publish these).

## Sync procedure

1. `ArtifactData` action `list`, collection `jobs`, `query.limit` 1000, `out_dir` = an empty scratch folder.
2. `python3 scripts/import_jobs.py <out_dir>/jobs`
3. `python3 build.py`
4. If `git status --porcelain` shows changes: commit (`Sinkron lowongan <YYYY-MM-DD>`) and push to `main`.
   Pages also changes daily because the "diperbarui" date and deadline badges are rebuilt; that is expected.

## Notes
- The public UI mirrors the Loker Sarjana review page (navy search band, field chips, card grid, side sheet). Keep them consistent when one changes.
- `import_jobs.py` strips reviewer notes (`Catatan review: ...`) from summaries; they must never reach the public site.
