#!/usr/bin/env python3
"""
Fetch and print the most recent GitHub Actions workflow run for a repository.

Defaults to yueneiqi/fd-test and uses the GitHub REST API. Authentication is
optional; set GITHUB_TOKEN to raise rate limits or access private runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from typing import Any, Iterable, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import zipfile


API_BASE = "https://api.github.com"
DEFAULT_REPO = "yueneiqi/fd-test"
REPO_ROOT = Path(__file__).resolve().parents[1]


def build_request(url: str, token: str | None) -> Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "buckal-actions-helper/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return Request(url, headers=headers)


def fetch_json(url: str, token: str | None) -> Tuple[Any, dict[str, str]]:
    req = build_request(url, token)
    with urlopen(req) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
        headers = {k: v for k, v in resp.headers.items()}
        return payload, headers


class NoRedirect(HTTPRedirectHandler):
    """Handler that prevents automatic redirects so we can capture Location."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_bytes(url: str, token: str | None) -> Tuple[bytes, dict[str, str]]:
    """
    Fetch bytes, following at most one external redirect (for Actions log blobs).
    GitHub's log endpoints return a 302 to a signed blob URL; we grab the
    Location ourselves to avoid auth issues and then fetch without credentials.
    """
    req = build_request(url, token)
    opener = build_opener(NoRedirect())
    try:
        with opener.open(req) as resp:
            content = resp.read()
            headers = {k: v for k, v in resp.headers.items()}
            return content, headers
    except HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            location = exc.headers.get("Location")
            if not location:
                raise
            # Follow the signed blob URL without GitHub auth headers.
            req2 = Request(
                location,
                headers={
                    "Accept": "*/*",
                    "User-Agent": "buckal-actions-helper/1.0",
                },
            )
            with urlopen(req2) as resp2:
                content = resp2.read()
                headers = {k: v for k, v in resp2.headers.items()}
                return content, headers
        raise


def parse_timestamp(ts: str | None) -> str:
    if not ts:
        return "unknown time"
    try:
        # GitHub timestamps are ISO8601 with Z; normalize for local display.
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        return ts


def make_date_slug(ts: str | None) -> str:
    if not ts:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%Y-%m-%d_%H-%M")
    except ValueError:
        return "unknown"


def safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", (name or "").strip())
    return cleaned or "job"


def latest_run(repo: str, token: str | None, branch: str | None) -> dict[str, Any] | None:
    params: dict[str, str] = {"per_page": "1"}
    if branch:
        params["branch"] = branch
    url = f"{API_BASE}/repos/{repo}/actions/runs"
    url = f"{url}?{urlencode(params)}"
    data, _ = fetch_json(url, token)
    runs = data.get("workflow_runs", [])
    if not runs:
        return None
    return runs[0]


def list_jobs(run_id: int, repo: str, token: str | None) -> list[dict[str, Any]]:
    url = f"{API_BASE}/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    data, _ = fetch_json(url, token)
    return data.get("jobs", [])


def iter_job_logs(job_id: int, repo: str, token: str | None) -> Iterable[tuple[str, str]]:
    """
    Yield (filename, text) pairs from the job log archive.

    GitHub returns a zip; we unzip and stream each file's contents.
    """
    url = f"{API_BASE}/repos/{repo}/actions/jobs/{job_id}/logs"
    raw, headers = fetch_bytes(url, token)
    ctype = headers.get("Content-Type", "")
    if "zip" not in ctype and not zipfile.is_zipfile(BytesIO(raw)):
        # Fallback: treat response as plain text
        yield ("job.log", raw.decode("utf-8", errors="replace"))
        return

    with zipfile.ZipFile(BytesIO(raw)) as zf:
        for name in sorted(zf.namelist()):
            with zf.open(name) as fp:
                text = fp.read().decode("utf-8", errors="replace")
                yield (name, text)


def format_run(run: dict[str, Any]) -> str:
    name = run.get("name") or "unknown workflow"
    status = run.get("status") or "unknown"
    conclusion = run.get("conclusion") or "pending"
    run_number = run.get("run_number", "n/a")
    event = run.get("event", "n/a")
    branch = run.get("head_branch", "n/a")
    sha = run.get("head_sha", "")[:7]
    html_url = run.get("html_url", "n/a")
    created_at = parse_timestamp(run.get("created_at"))
    message = ""
    head_commit = run.get("head_commit") or {}
    msg_text = head_commit.get("message")
    if msg_text:
        first_line = msg_text.splitlines()[0]
        message = f'commit: {first_line}'
    lines = [
        f"workflow : {name}",
        f"run      : #{run_number} ({event} on {branch})",
        f"status   : {status} / {conclusion}",
        f"created  : {created_at}",
        f"sha      : {sha}",
    ]
    if message:
        lines.append(message)
    lines.append(f"url      : {html_url}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="owner/repo to query (default: yueneiqi/fd-test)",
    )
    parser.add_argument(
        "--branch",
        help="optional branch filter",
    )
    parser.add_argument(
        "--token",
        help="GitHub token; falls back to GITHUB_TOKEN or GITHUB_ACCESS_TOKEN env vars",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print raw JSON for the latest run",
    )
    parser.add_argument(
        "--dump-log",
        action="store_true",
        help="download logs for jobs whose name starts with 'b2'; saves failed job logs to files",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")

    if args.dump_log and not token:
        sys.exit(
            "Log download requires authentication. Set --token, GITHUB_TOKEN, or GITHUB_ACCESS_TOKEN with actions:read scope."
        )

    try:
        run = latest_run(args.repo, token, args.branch)
    except HTTPError as exc:
        sys.exit(f"GitHub API error ({exc.code}): {exc.reason}")
    except URLError as exc:
        sys.exit(f"Network error: {exc.reason}")
    except Exception as exc:  # pragma: no cover - guard rail
        sys.exit(f"Unexpected error: {exc}")

    if not run:
        sys.exit(f"No workflow runs found for {args.repo}")

    if args.json:
        print(json.dumps(run, indent=2))
    else:
        print(format_run(run))

    if args.dump_log:
        jobs = list_jobs(run["id"], args.repo, token)
        matched = [j for j in jobs if str(j.get("name", "")).startswith("b2")]
        if not matched:
            print("No jobs with name starting with 'b2' found.", file=sys.stderr)
            return

        date_slug = make_date_slug(run.get("created_at"))
        log_dir = REPO_ROOT / "log" / date_slug
        log_dir.mkdir(parents=True, exist_ok=True)

        for job in matched:
            jname = job.get("name", "unknown")
            jid = job.get("id")
            conclusion = (job.get("conclusion") or "").lower()

            if conclusion == "success":
                print(f"job '{jname}' succeeded; logs not fetched")
                continue

            try:
                log_parts: list[str] = []
                for fname, text in iter_job_logs(int(jid), args.repo, token):
                    log_parts.append(f"# {fname}\n{text}")
                combined = "\n\n".join(log_parts).rstrip() + "\n"
                out_path = log_dir / f"{safe_name(jname)}_{jid}.log"
                out_path.write_text(combined, encoding="utf-8", errors="replace", newline="\n")
                print(f"job '{jname}' failed; logs written to {out_path}")
            except Exception as exc:  # pragma: no cover - log download edge cases
                err_path = log_dir / f"{safe_name(jname)}_{jid}.err.log"
                err_path.write_text(
                    f"Error fetching logs for job {jid}: {exc}\n",
                    encoding="utf-8",
                    errors="replace",
                    newline="\n",
                )
                print(
                    f"Failed to fetch logs for job {jid}: {exc} (saved to {err_path})",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    main()
