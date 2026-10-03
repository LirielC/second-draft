import pytest
from second_draft.archive import Archive

@pytest.fixture
def archive(tmp_path):
    return Archive(tmp_path / "projects.db")

def project(archive, title="Recipe Finder"):
    return archive.create(title, "Search recipes by ingredients", "Too much manual entry", reusable_parts=["Ingredient search"], tags=["Python"])

def test_persistence(tmp_path):
    path = tmp_path / "archive.db"
    saved = project(Archive(path))
    assert Archive(path).get(saved["id"]) == saved

def test_search_literal_and_case_insensitive(archive):
    saved = project(archive)
    assert archive.search("PYTHON ingredient")[0]["id"] == saved["id"]
    assert archive.search("' OR 1=1 --") == []
    assert archive.search("%") == []

def test_update_preserves_identity_and_rejects_stale_revision(archive):
    saved = project(archive)
    updated = archive.update(saved["id"], {"status": "revived"}, 1)
    assert updated["created_at"] == saved["created_at"]
    assert updated["revision"] == 2
    assert archive.search(status="archived") == []
    with pytest.raises(ValueError, match="changed"):
        archive.update(saved["id"], {"title": "Stale"}, 1)
    assert archive.get(saved["id"])["title"] == saved["title"]

@pytest.mark.parametrize("changes", [{"id": "override"}, {"status": "invalid"}, {"title": " "}, {"tags": "python"}, {"repository_url": "http://example.com"}])
def test_invalid_updates(archive, changes):
    saved = project(archive)
    with pytest.raises(ValueError):
        archive.update(saved["id"], changes, 1)
    assert archive.get(saved["id"])["revision"] == 1

def test_missing_project(archive):
    with pytest.raises(ValueError, match="not found"):
        archive.get("missing")

def test_remix_has_evidence_and_does_not_write(archive):
    first = project(archive)
    second = project(archive, "Shopping List")
    result = archive.remix([first["id"], second["id"]], "Build a pantry planner", 6)
    assert {p["id"] for p in result["sources"]} == {first["id"], second["id"]}
    assert result["time_budget_hours"] == 6
    assert len(archive.search()) == 2
    with pytest.raises(ValueError):
        archive.remix([first["id"], first["id"]], "Goal")

def test_empty_required_input(archive):
    with pytest.raises(ValueError):
        archive.create("", "Description", "Reason")
