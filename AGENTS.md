# Project Overview: `vuuminhphuoc/vuuminhphuoc`

This repository serves as the special GitHub Profile README repository for user [`vuuminhphuoc`](https://github.com/vuuminhphuoc).
Its primary role is to dynamically generate and display personalized stats (lines of code, commits, stars, account age) in SVG badges for both light and dark mode on the GitHub profile page.

---

## Repository Structure

- `README.md`: Minimal HTML/markdown rendering `<picture>` pointing to `dark_mode.svg` and `light_mode.svg`.
- `today.py`: Core Python script responsible for fetching GitHub account data, GraphQL statistics, lines of code, commit counts, and dynamically rewriting SVG graphics (`light_mode.svg` & `dark_mode.svg`).
- `light_mode.svg` / `dark_mode.svg`: Generated SVG templates showing live stats.
- `cache/`: Contains cached response hashes and `requirements.txt`.
- `.github/workflows/build.yaml`: GitHub Actions cron workflow running daily (`0 4 * * *`) and on push/dispatch to update profile stats and commit changes back to `main`.

---

## AI Agent Guidelines & Architecture Rules

### 1. File Modification Safeguards
- **DO NOT** replace `README.md` with standard text/markdown profile layouts unless specifically instructed by the owner. It must remain a clean image/SVG container for GitHub profile rendering.
- **DO NOT** hardcode secrets or personal access tokens into `today.py`. All GitHub GraphQL / REST requests must consume `ACCESS_TOKEN` and `USER_NAME` via environment variables.

### 2. Runtime & Dependencies
- Python version: `>= 3.11`
- Dependencies (`cache/requirements.txt`):
  - `python-dateutil`
  - `requests`
  - `lxml`

### 3. Workflow Invariants (`.github/workflows/build.yaml`)
- The GitHub Actions workflow executes on `ubuntu-latest`.
- Actions required permissions: `contents: write`.
- If Git commit/push fails in GitHub Actions with `fatal error in commit_refs`, it is typically a transient GitHub remote ref lock / network hiccup — trigger a manual re-run with `gh workflow run build.yaml --repo vuuminhphuoc/vuuminhphuoc`.

### 4. Local Execution & Testing
To test `today.py` locally:
```bash
python -m pip install -r cache/requirements.txt
# Set environment variables:
export ACCESS_TOKEN="<your_github_pat>"
export USER_NAME="vuuminhphuoc"
python today.py
```
*(On Windows PowerShell: `$env:ACCESS_TOKEN="..."; $env:USER_NAME="vuuminhphuoc"; python today.py`)*
