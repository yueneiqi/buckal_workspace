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
from typing import Any, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://api.github.com"
DEFAULT_REPO = "yueneiqi/fd-test"


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


def parse_timestamp(ts: str | None) -> str:
    if not ts:
        return "unknown time"
    try:
        # GitHub timestamps are ISO8601 with Z; normalize for local display.
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        return ts


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
        help="GitHub token; falls back to GITHUB_TOKEN env var",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print raw JSON for the latest run",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN")

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


if __name__ == "__main__":
    main()
