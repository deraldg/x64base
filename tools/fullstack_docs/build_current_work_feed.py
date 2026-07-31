#!/usr/bin/env python3
"""Build the public-safe current work feed from LabTalk project/task registries."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TASK_FIELDS = {
    "id",
    "title",
    "ticket",
    "kind",
    "project_ids",
    "channel",
    "status",
    "owner",
    "updated_on",
    "truth_state",
    "proof_state",
    "next_gate",
    "summary",
    "website_paths",
}
ALLOWED_CHANNELS = {"ai_portal", "pseudo_chat"}


def require_python_312() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"Current-work feed requires Python 3.12; running {sys.version_info.major}.{sys.version_info.minor}."
        )


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def validate(projects_doc: dict[str, Any], tasks_doc: dict[str, Any]) -> None:
    projects = projects_doc.get("projects")
    tasks = tasks_doc.get("tasks")
    if not isinstance(projects, list) or not projects:
        raise ValueError("projects.yaml must contain a non-empty projects list")
    if tasks_doc.get("schema") != "labtalk.ai_portal.tasks.v1":
        raise ValueError("unexpected task registry schema")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("task registry must contain a non-empty tasks list")

    project_ids = [project.get("id") for project in projects]
    if len(project_ids) != len(set(project_ids)):
        raise ValueError("duplicate project id")
    known_projects = set(project_ids)
    task_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("every task must be a mapping")
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            raise ValueError(f"{task.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if task["id"] in task_ids:
            raise ValueError(f"duplicate task id: {task['id']}")
        task_ids.add(task["id"])
        if task["channel"] not in ALLOWED_CHANNELS:
            raise ValueError(f"{task['id']} has unsupported channel {task['channel']}")
        unknown = set(task["project_ids"]) - known_projects
        if unknown:
            raise ValueError(f"{task['id']} references unknown projects: {sorted(unknown)}")
        for website_path in task["website_paths"]:
            if not isinstance(website_path, str) or not website_path.startswith("/"):
                raise ValueError(f"{task['id']} has invalid public website path")


def public_projection(projects_doc: dict[str, Any], tasks_doc: dict[str, Any]) -> dict[str, Any]:
    projects = [
        {
            "id": project["id"],
            "name": project["name"],
            "kind": project["kind"],
            "status": project["status"],
        }
        for project in projects_doc["projects"]
    ]
    tasks = [
        {
            key: task[key]
            for key in (
                "id",
                "title",
                "ticket",
                "kind",
                "project_ids",
                "channel",
                "status",
                "owner",
                "updated_on",
                "truth_state",
                "proof_state",
                "next_gate",
                "summary",
                "website_paths",
            )
        }
        for task in tasks_doc["tasks"]
    ]
    return {
        "schema": "x64base.current_work.v1",
        "as_of_date": tasks_doc["as_of_date"],
        "maintenance_class": "maintained_current",
        "publication_state": tasks_doc["current_documentation_flush"]["publication_state"],
        "authority": tasks_doc["authority"],
        "current_documentation_flush": tasks_doc["current_documentation_flush"],
        "summary": {
            "projects": len(projects),
            "tasks": len(tasks),
            "task_statuses": dict(sorted(Counter(task["status"] for task in tasks).items())),
            "pseudo_chat_inbox": sum(task["channel"] == "pseudo_chat" for task in tasks),
        },
        "projects": projects,
        "tasks": tasks,
    }


def escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_mdx(feed: dict[str, Any]) -> str:
    flush = feed["current_documentation_flush"]
    project_by_id = {project["id"]: project["name"] for project in feed["projects"]}
    task_rows = []
    for task in feed["tasks"]:
        projects = ", ".join(project_by_id[pid] for pid in task["project_ids"])
        links = " · ".join(
            f"[open]({path})" for path in task["website_paths"]
        ) or "—"
        task_rows.append(
            "| {ticket} | {title} | `{status}` | {owner} | {projects} | {next_gate} | {links} |".format(
                ticket=escape_cell(task["ticket"]),
                title=escape_cell(task["title"]),
                status=escape_cell(task["status"]),
                owner=escape_cell(task["owner"]),
                projects=escape_cell(projects),
                next_gate=escape_cell(task["next_gate"]),
                links=links,
            )
        )

    project_rows = [
        f"| {escape_cell(project['name'])} | `{escape_cell(project['status'])}` | {escape_cell(project['kind'])} |"
        for project in feed["projects"]
    ]
    pseudo = [task for task in feed["tasks"] if task["channel"] == "pseudo_chat"]
    pseudo_rows = [
        f"| {escape_cell(task['ticket'])} | {escape_cell(task['title'])} | `{escape_cell(task['status'])}` | {escape_cell(task['next_gate'])} |"
        for task in pseudo
    ]
    status_counts = ", ".join(
        f"`{status}` {count}" for status, count in feed["summary"]["task_statuses"].items()
    )

    mg = flush.get("manualgen_command_reference_lane")
    if mg:
        manualgen_section = (
            "## Manualgen command-reference lane\n\n"
            f"{mg.get('label', '')}\n\n"
            "| Field | Value |\n| --- | --- |\n"
            f"| Run / harvest | `{mg.get('run_id', '')}` / `{mg.get('harvest', '')}` |\n"
            f"| HELP | {mg.get('help_topics', '')} topics / {mg.get('help_lines', 0):,} lines |\n"
            f"| Command reference | {mg.get('command_reference_pages', '')} pages / {mg.get('command_lineage_rows', 0):,} lineage rows |\n"
            f"| Catalogs | SYSCMD {mg.get('syscmd', '')} / SYSFUNC {mg.get('sysfunc', '')} |\n"
            f"| Functions accepted | {mg.get('functions_accepted', '')} ({mg.get('functions', '')}) |\n"
            f"| Gate 4 | `{mg.get('gate4', '')}` ({mg.get('gate4_apply_run', '')}) |\n"
            f"| Publication readiness | `{mg.get('publication_readiness', '')}` |\n"
            f"| State | `{mg.get('publication_state', '')}` |\n\n"
            f"{mg.get('note', '')}\n\n"
        )
    else:
        manualgen_section = ""

    return f"""---
title: "Current Tasks & Projects"
description: "Maintained current-state view of AI Portal tasks, project lanes, tickets, Pseudo-Chat returns, evidence state, and next gates."
---

> **As of {feed['as_of_date']} · maintenance class `maintained_current`.**
> This is a permanent route with a replaceable present-state region. Event history
> remains in the linked intake, proof, and closeout records.

## What this page is

This is the human-viewable projection of the AI Portal project and task registries.
It answers four operational questions: **what is active, who owns it, what has been
proved, and what gate comes next**. Pseudo-Chat is represented here as an asynchronous
return inbox; it is not a second task authority.

Website status is reporting only. It does not commit source, publish a release, or
promote a local proof into public runtime truth.

## Documentation flush at a glance

| Field | Current value |
| --- | --- |
| Run | `{flush['run_id']}` / `{flush['ticket']}` |
| State | `{flush['state']}` |
| Publication | `{flush['publication_state']}` |
| Source contracts | {flush['source_contracts']} |
| HELP | {flush['help_topics']} topics / {flush['help_lines']:,} lines |
| Command reference | {flush['command_reference_pages']} pages / {flush['command_lineage_rows']:,} lineage rows |
| Assembled manual | {flush['manual_parts']} parts / {flush['manual_lines']:,} lines / {flush['manual_pdf_pages']} PDF pages |
| Next gate | {flush['next_gate']} |

[Inspect the complete vertical](/docs/dev/full-stack-documentation-push) ·
[Open documentation progress](/docs/dev/documentation-progress) ·
[Review the assembled manual](/docs/dev/developer-manual)

{manualgen_section}## Current tickets and tasks

**{len(feed['tasks'])} tracked tasks.** Status distribution: {status_counts}.

| Ticket | Task | Status | Owner | Project(s) | Next gate | Review |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(task_rows)}

## Pseudo-Chat return inbox

The Pseudo-Chat lane carries reviewed external replies back into the Portal. A return
stays here until it is corrected, promoted into a governed task, or explicitly closed.

| Ticket | Return | Status | Required next action |
| --- | --- | --- | --- |
{chr(10).join(pseudo_rows) if pseudo_rows else '| — | No returns waiting | — | — |'}

[Read the full Pseudo-Chat log](/docs/labtalk/agent-sync).

## Registered projects

These are project-level containers, not claims that every child lane is complete.

| Project | Registry status | Kind |
| --- | --- | --- |
{chr(10).join(project_rows)}

## Maintenance contract

- Refresh this page from the registries during every full-stack documentation push
  and at a governed task closeout that changes status or next gate.
- Advance the **as-of date** only when the registry is reconciled.
- Keep historical event dates in their original records; do not rewrite them to look
  current.
- Retain `Unverified`, `backlog`, `proposed`, and `not deployed` labels until their
  named proof or promotion gate closes.
- The machine-readable companion is
  [current-work-v1.json](/artifacts/current-work-v1.json).
"""


def main() -> int:
    require_python_312()
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-mdx", type=Path, required=True)
    args = parser.parse_args()

    projects_doc = load_yaml(args.projects)
    tasks_doc = load_yaml(args.tasks)
    validate(projects_doc, tasks_doc)
    feed = public_projection(projects_doc, tasks_doc)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_mdx.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
    args.out_mdx.write_text(render_mdx(feed), encoding="utf-8")
    print(
        f"PASS current-work feed: {feed['summary']['projects']} projects, "
        f"{feed['summary']['tasks']} tasks, as_of={feed['as_of_date']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
