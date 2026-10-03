"""Persistent project archive. No model calls or external network access."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

FIELDS = {"title", "description", "pause_reason", "lessons_learned", "reusable_parts", "tags", "repository_url", "status"}
LIST_FIELDS = {"lessons_learned", "reusable_parts", "tags"}

class Archive:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def validate(self, values):
        if set(values) - FIELDS:
            raise ValueError("Unknown project fields")
        for field, value in values.items():
            if field in LIST_FIELDS:
                if not isinstance(value, list) or len(value) > 50 or any(not isinstance(item, str) or not item.strip() or len(item) > 2000 for item in value):
                    raise ValueError(f"{field} must contain up to 50 nonempty strings")
            elif not isinstance(value, str) or len(value) > 10000:
                raise ValueError(f"{field} must be a string of at most 10000 characters")
        for field in ("title", "description", "pause_reason"):
            if field in values and not values[field].strip():
                raise ValueError(f"{field} cannot be empty")
        if "status" in values and values["status"] not in {"archived", "revived", "completed"}:
            raise ValueError("Status must be archived, revived, or completed")
        url = values.get("repository_url", "")
        if url and not url.startswith("https://"):
            raise ValueError("Repository URL must use HTTPS")

    def create(self, title, description, pause_reason, lessons_learned=None, reusable_parts=None, tags=None, repository_url=""):
        values = dict(title=title, description=description, pause_reason=pause_reason,
                      lessons_learned=lessons_learned or [], reusable_parts=reusable_parts or [],
                      tags=tags or [], repository_url=repository_url, status="archived")
        self.validate(values)
        now = datetime.now(timezone.utc).isoformat()
        project = dict(id=str(uuid4()), **values, created_at=now, updated_at=now, revision=1)
        with self.connect() as db:
            db.execute("INSERT INTO projects VALUES (?, ?)", (project["id"], json.dumps(project)))
        return project

    def get(self, project_id):
        with self.connect() as db:
            row = db.execute("SELECT data FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            raise ValueError("Project not found")
        return json.loads(row[0])

    def search(self, query="", status=None, limit=20):
        if not isinstance(query, str) or len(query) > 500:
            raise ValueError("Query must be a string of at most 500 characters")
        if status is not None and status not in {"archived", "revived", "completed"}:
            raise ValueError("Invalid status")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        with self.connect() as db:
            projects = [json.loads(row[0]) for row in db.execute("SELECT data FROM projects")]
        terms = query.casefold().split()
        matches = []
        for project in projects:
            searchable = " ".join(str(project[field]) for field in FIELDS).casefold()
            if (status is None or project["status"] == status) and all(term in searchable for term in terms):
                matches.append(project)
        return sorted(matches, key=lambda p: p["updated_at"], reverse=True)[:limit]

    def update(self, project_id, changes, expected_revision):
        if not changes:
            raise ValueError("Provide at least one changed field")
        self.validate(changes)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                raise ValueError("Project not found")
            project = json.loads(row[0])
            if project["revision"] != expected_revision:
                raise ValueError("Project changed; retrieve it again before updating")
            project.update(changes)
            project["revision"] += 1
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            db.execute("UPDATE projects SET data = ? WHERE id = ?", (json.dumps(project), project_id))
        return project

    def remix(self, project_ids, goal, time_budget_hours=8):
        if len(set(project_ids)) != len(project_ids) or not 2 <= len(project_ids) <= 5:
            raise ValueError("Select 2 to 5 distinct projects")
        if not goal.strip() or len(goal) > 2000 or not 1 <= time_budget_hours <= 80:
            raise ValueError("Provide a goal and a time budget between 1 and 80 hours")
        projects = [self.get(project_id) for project_id in project_ids]
        return {"goal": goal, "time_budget_hours": time_budget_hours,
                "sources": projects,
                "instructions": "Propose one small project using recorded reusable parts. Cite source project IDs for each reused piece. Separate recorded facts from assumptions. Provide a first step, scope cuts, and an estimated plan; estimates are not guarantees. Do not claim to have inspected repository files."}
