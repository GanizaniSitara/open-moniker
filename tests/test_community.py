"""Tests for the community contributions module.

Run: C:/miniconda3/envs/python312/python.exe -m pytest tests/test_community.py -v
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_SRC, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from moniker_svc.community.registry import CommunityRegistry
from moniker_svc.community.storage import FileStorage
from moniker_svc.community.types import EntityContributions, Flag, Suggestion


# ===================================================================
# Storage tests
# ===================================================================

class TestFileStorage:
    """Round-trip and atomic write tests for FileStorage."""

    def test_save_and_load_flags(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        # Create some flags
        f1 = registry.create_flag("moniker", "pricing.fx.spot", "outdated", "alice", comment="stale")
        f2 = registry.create_flag("moniker", "pricing.fx.spot", "incorrect", "bob")

        # Save
        contrib = registry.dump_entity("moniker", "pricing.fx.spot")
        assert contrib is not None
        storage.save_entity("moniker", "pricing.fx.spot", contrib)

        # Verify files exist on disk
        flags_path = tmp_path / "entities" / "moniker" / "pricing.fx.spot" / "flags.json"
        assert flags_path.exists()

        # Verify JSON content
        data = json.loads(flags_path.read_text(encoding="utf-8"))
        assert len(data["flags"]) == 2
        assert data["flags"][0]["flagType"] in ("outdated", "incorrect")

        # Load into fresh registry
        registry2 = CommunityRegistry()
        loaded = storage.load_entity("moniker", "pricing.fx.spot")
        assert loaded is not None
        registry2.load_entity("moniker", "pricing.fx.spot", loaded)

        flags = registry2.get_flags("moniker", "pricing.fx.spot")
        assert len(flags) == 2
        flag_types = {f.flag_type for f in flags}
        assert flag_types == {"outdated", "incorrect"}

    def test_save_and_load_suggestions(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        registry.create_suggestion(
            "moniker", "pricing.fx.spot", "description",
            "Real-time FX spot rates", "alice",
            current_value="FX spot rates", reason="More precise",
        )

        contrib = registry.dump_entity("moniker", "pricing.fx.spot")
        storage.save_entity("moniker", "pricing.fx.spot", contrib)

        loaded = storage.load_entity("moniker", "pricing.fx.spot")
        assert loaded is not None
        assert len(loaded.suggestions) == 1
        s = list(loaded.suggestions.values())[0]
        assert s.field_name == "description"
        assert s.proposed_value == "Real-time FX spot rates"
        assert s.current_value == "FX spot rates"

    def test_save_and_load_annotations_with_votes(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        a = registry.create_annotation(
            "moniker", "pricing.fx.spot", "tip",
            "Use T+1 settlement date", "alice",
        )
        registry.upvote_annotation(a.id, "bob")
        registry.upvote_annotation(a.id, "charlie")

        contrib = registry.dump_entity("moniker", "pricing.fx.spot")
        storage.save_entity("moniker", "pricing.fx.spot", contrib)

        loaded = storage.load_entity("moniker", "pricing.fx.spot")
        assert loaded is not None
        ann = list(loaded.annotations.values())[0]
        assert ann.upvote_count == 2
        assert len(ann.votes) == 2
        voters = {v.voter for v in ann.votes}
        assert voters == {"bob", "charlie"}

    def test_save_and_load_discussions_with_replies(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        d = registry.create_discussion(
            "moniker", "pricing.fx.spot",
            "Should we split this?", "alice",
        )
        registry.add_reply(d.id, "Yes, schemas differ", "bob")
        registry.add_reply(d.id, "I agree", "charlie", parent_reply_id=d.replies[0].id if d.replies else None)

        contrib = registry.dump_entity("moniker", "pricing.fx.spot")
        storage.save_entity("moniker", "pricing.fx.spot", contrib)

        loaded = storage.load_entity("moniker", "pricing.fx.spot")
        assert loaded is not None
        disc = list(loaded.discussions.values())[0]
        assert disc.title == "Should we split this?"
        assert len(disc.replies) == 2

    def test_save_and_load_helpful_votes(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        registry.submit_helpful_vote("moniker", "pricing.fx.spot", True, author="alice")
        registry.submit_helpful_vote("moniker", "pricing.fx.spot", False, comment="confusing", author="bob")

        contrib = registry.dump_entity("moniker", "pricing.fx.spot")
        storage.save_entity("moniker", "pricing.fx.spot", contrib)

        loaded = storage.load_entity("moniker", "pricing.fx.spot")
        assert loaded is not None
        assert len(loaded.helpful_votes) == 2

    def test_load_all(self, tmp_path):
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()

        registry.create_flag("moniker", "pricing.fx.spot", "outdated", "alice")
        registry.create_flag("moniker", "pricing.fx.forward", "missing", "bob")
        registry.create_flag("model", "risk.var", "incorrect", "charlie")

        for et, ek in registry.all_entity_keys():
            contrib = registry.dump_entity(et, ek)
            storage.save_entity(et, ek, contrib)

        all_data = storage.load_all()
        assert len(all_data) == 3
        assert ("moniker", "pricing.fx.spot") in all_data
        assert ("moniker", "pricing.fx.forward") in all_data
        assert ("model", "risk.var") in all_data

    def test_load_missing_entity_returns_none(self, tmp_path):
        storage = FileStorage(tmp_path)
        assert storage.load_entity("moniker", "nonexistent") is None

    def test_atomic_write_creates_no_tmp_files(self, tmp_path):
        """Verify .tmp files are cleaned up after atomic write."""
        storage = FileStorage(tmp_path)
        registry = CommunityRegistry()
        registry.create_flag("moniker", "test", "outdated", "alice")
        contrib = registry.dump_entity("moniker", "test")
        storage.save_entity("moniker", "test", contrib)

        entity_dir = tmp_path / "entities" / "moniker" / "test"
        tmp_files = list(entity_dir.glob("*.tmp"))
        assert tmp_files == [], f"Leftover .tmp files: {tmp_files}"


# ===================================================================
# Registry tests
# ===================================================================

class TestCommunityRegistry:
    """Thread-safe registry CRUD and constraint tests."""

    def test_create_and_get_flags(self):
        reg = CommunityRegistry()
        f = reg.create_flag("moniker", "a.b.c", "outdated", "alice")
        assert f.id
        assert f.flag_type == "outdated"
        assert f.status == "open"

        flags = reg.get_flags("moniker", "a.b.c")
        assert len(flags) == 1
        assert flags[0].id == f.id

    def test_flag_summary(self):
        reg = CommunityRegistry()
        reg.create_flag("moniker", "a.b.c", "outdated", "alice")
        reg.create_flag("moniker", "a.b.c", "outdated", "bob")
        reg.create_flag("moniker", "a.b.c", "incorrect", "charlie")

        summary = reg.get_flag_summary("moniker", "a.b.c")
        assert summary["total"] == 3
        assert summary["byType"]["outdated"] == 2
        assert summary["byType"]["incorrect"] == 1

    def test_update_flag_status(self):
        reg = CommunityRegistry()
        f = reg.create_flag("moniker", "a.b.c", "outdated", "alice")
        updated = reg.update_flag_status(f.id, "resolved", resolved_by="admin")
        assert updated is not None
        assert updated.status == "resolved"
        assert updated.resolved_by == "admin"
        assert updated.resolved_at is not None

    def test_update_nonexistent_flag_returns_none(self):
        reg = CommunityRegistry()
        assert reg.update_flag_status("nonexistent", "resolved") is None

    def test_create_and_get_suggestions(self):
        reg = CommunityRegistry()
        s = reg.create_suggestion(
            "moniker", "a.b.c", "description", "new desc", "alice",
            current_value="old desc", reason="clarity",
        )
        assert s.status == "pending"
        suggestions = reg.get_suggestions("moniker", "a.b.c")
        assert len(suggestions) == 1

    def test_approve_and_reject_suggestion(self):
        reg = CommunityRegistry()
        s = reg.create_suggestion("moniker", "a.b.c", "desc", "new", "alice")

        approved = reg.approve_suggestion(s.id, "admin", "looks good")
        assert approved.status == "approved"
        assert approved.reviewed_by == "admin"

        s2 = reg.create_suggestion("moniker", "a.b.c", "other", "val", "bob")
        rejected = reg.reject_suggestion(s2.id, "admin", "not needed")
        assert rejected.status == "rejected"

    def test_upvote_uniqueness(self):
        """Same voter cannot upvote twice (Prisma @@unique equivalent)."""
        reg = CommunityRegistry()
        a = reg.create_annotation("moniker", "a.b.c", "tip", "content", "alice")

        assert reg.upvote_annotation(a.id, "bob") is True
        assert reg.upvote_annotation(a.id, "bob") is False  # duplicate
        assert reg.upvote_annotation(a.id, "charlie") is True

        anns = reg.get_annotations("moniker", "a.b.c")
        assert anns[0].upvote_count == 2

    def test_remove_upvote(self):
        reg = CommunityRegistry()
        a = reg.create_annotation("moniker", "a.b.c", "tip", "content", "alice")
        reg.upvote_annotation(a.id, "bob")

        assert reg.remove_upvote(a.id, "bob") is True
        assert reg.remove_upvote(a.id, "bob") is False  # already removed

        anns = reg.get_annotations("moniker", "a.b.c")
        assert anns[0].upvote_count == 0

    def test_annotations_sorted_by_upvotes(self):
        reg = CommunityRegistry()
        a1 = reg.create_annotation("moniker", "a.b.c", "tip", "low", "alice")
        a2 = reg.create_annotation("moniker", "a.b.c", "warning", "high", "bob")
        reg.upvote_annotation(a2.id, "charlie")
        reg.upvote_annotation(a2.id, "dave")

        anns = reg.get_annotations("moniker", "a.b.c")
        assert anns[0].id == a2.id  # more upvotes first

    def test_discussion_with_replies(self):
        reg = CommunityRegistry()
        d = reg.create_discussion("moniker", "a.b.c", "Split this?", "alice")
        r = reg.add_reply(d.id, "Yes please", "bob")
        assert r is not None
        assert r.author == "bob"

        detail = reg.get_discussion(d.id)
        assert detail is not None
        assert len(detail.replies) == 1

    def test_nested_replies(self):
        reg = CommunityRegistry()
        d = reg.create_discussion("moniker", "a.b.c", "Topic", "alice")
        r1 = reg.add_reply(d.id, "First reply", "bob")
        r2 = reg.add_reply(d.id, "Reply to first", "charlie", parent_reply_id=r1.id)

        detail = reg.get_discussion(d.id)
        assert len(detail.replies) == 2
        assert detail.replies[1].parent_reply_id == r1.id

    def test_add_reply_to_nonexistent_discussion(self):
        reg = CommunityRegistry()
        assert reg.add_reply("nonexistent", "text", "alice") is None

    def test_helpful_summary(self):
        reg = CommunityRegistry()
        reg.submit_helpful_vote("moniker", "a.b.c", True, author="alice")
        reg.submit_helpful_vote("moniker", "a.b.c", True, author="bob")
        reg.submit_helpful_vote("moniker", "a.b.c", False, author="charlie")

        summary = reg.get_helpful_summary("moniker", "a.b.c")
        assert summary == {"helpful": 2, "notHelpful": 1, "total": 3}

    def test_activity_summary(self):
        reg = CommunityRegistry()
        reg.create_flag("moniker", "a.b.c", "outdated", "alice")
        reg.create_suggestion("moniker", "a.b.c", "desc", "new", "bob")
        reg.create_annotation("moniker", "a.b.c", "tip", "content", "charlie")
        reg.create_discussion("moniker", "a.b.c", "Topic", "dave")

        summary = reg.get_activity_summary("moniker", "a.b.c")
        assert summary == {"flags": 1, "suggestions": 1, "annotations": 1, "discussions": 1, "total": 4}

    def test_empty_entity_returns_empty(self):
        reg = CommunityRegistry()
        assert reg.get_flags("moniker", "nonexistent") == []
        assert reg.get_suggestions("moniker", "nonexistent") == []
        assert reg.get_annotations("moniker", "nonexistent") == []
        assert reg.get_discussions("moniker", "nonexistent") == []
        assert reg.get_helpful_summary("moniker", "nonexistent") == {"helpful": 0, "notHelpful": 0, "total": 0}
        assert reg.get_activity_summary("moniker", "nonexistent") == {
            "flags": 0, "suggestions": 0, "annotations": 0, "discussions": 0, "total": 0,
        }

    def test_thread_safety_concurrent_writes(self):
        """Hammer the registry from multiple threads to check for data corruption."""
        reg = CommunityRegistry()
        errors = []

        def create_flags(n):
            try:
                for i in range(100):
                    reg.create_flag("moniker", "stress", "outdated", f"user-{n}-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_flags, args=(t,)) for t in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        flags = reg.get_flags("moniker", "stress")
        assert len(flags) == 1000  # 10 threads x 100 flags


# ===================================================================
# Config snapshot storage tests
# ===================================================================

class TestConfigSnapshots:
    def test_save_and_load_snapshot(self, tmp_path):
        from moniker_svc.community.types import SharedConfig

        storage = FileStorage(tmp_path)
        sc = SharedConfig(
            id="abc123",
            title="Test Config",
            author="alice",
            description="A test",
            moniker_count=42,
            created_at="2026-03-25T10:00:00Z",
            updated_at="2026-03-25T10:00:00Z",
        )
        catalog_yaml = "pricing.fx.spot:\n  source_type: snowflake\n"

        storage.save_config_snapshot(sc, catalog_yaml)

        result = storage.load_config_snapshot("abc123")
        assert result is not None
        loaded_sc, loaded_yaml = result
        assert loaded_sc.title == "Test Config"
        assert loaded_sc.moniker_count == 42
        assert "pricing.fx.spot" in loaded_yaml

    def test_list_snapshots(self, tmp_path):
        from moniker_svc.community.types import SharedConfig

        storage = FileStorage(tmp_path)
        for i, status in enumerate(["draft", "published", "draft"]):
            sc = SharedConfig(
                id=f"cfg-{i}",
                title=f"Config {i}",
                author="alice",
                status=status,
                created_at=f"2026-03-25T1{i}:00:00Z",
                updated_at=f"2026-03-25T1{i}:00:00Z",
            )
            storage.save_config_snapshot(sc, "monikers: {}")

        all_configs = storage.list_config_snapshots()
        assert len(all_configs) == 3

        published = storage.list_config_snapshots(status="published")
        assert len(published) == 1
        assert published[0].status == "published"

    def test_update_metadata(self, tmp_path):
        from moniker_svc.community.types import SharedConfig

        storage = FileStorage(tmp_path)
        sc = SharedConfig(
            id="upd-1", title="Original", author="alice",
            created_at="2026-03-25T10:00:00Z", updated_at="2026-03-25T10:00:00Z",
        )
        storage.save_config_snapshot(sc, "yaml: content")

        sc.status = "published"
        sc.published_at = "2026-03-25T11:00:00Z"
        storage.update_config_metadata(sc)

        result = storage.load_config_snapshot("upd-1")
        assert result is not None
        loaded, _ = result
        assert loaded.status == "published"
        assert loaded.published_at == "2026-03-25T11:00:00Z"

    def test_load_nonexistent_returns_none(self, tmp_path):
        storage = FileStorage(tmp_path)
        assert storage.load_config_snapshot("nope") is None
        assert storage.read_config_catalog_yaml("nope") is None


# ===================================================================
# Route integration tests (FastAPI TestClient, sync)
# ===================================================================

class TestCommunityRoutes:
    """Test the HTTP endpoints via FastAPI TestClient."""

    @pytest.fixture(autouse=True)
    def setup_app(self, tmp_path):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from moniker_svc.community.registry import CommunityRegistry
        from moniker_svc.community.routes import configure, router
        from moniker_svc.community.storage import FileStorage

        app = FastAPI()
        app.include_router(router)

        reg = CommunityRegistry()
        store = FileStorage(tmp_path)
        configure(registry=reg, storage=store)

        self.client = TestClient(app)
        self.tmp_path = tmp_path

    def test_create_and_get_flags(self):
        r = self.client.post("/community/flags", json={
            "entityType": "moniker",
            "entityKey": "pricing.fx.spot",
            "flagType": "outdated",
            "author": "alice",
            "comment": "stale data",
        })
        assert r.status_code == 201
        flag = r.json()
        assert flag["flagType"] == "outdated"
        assert flag["author"] == "alice"
        assert flag["status"] == "open"
        assert "id" in flag

        # GET
        r = self.client.get("/community/flags", params={
            "entityType": "moniker", "entityKey": "pricing.fx.spot",
        })
        assert r.status_code == 200
        flags = r.json()
        assert len(flags) == 1
        assert flags[0]["id"] == flag["id"]

        # Verify camelCase keys
        assert "entityType" in flags[0]
        assert "flagType" in flags[0]
        assert "createdAt" in flags[0]

    def test_flag_summary(self):
        for ft in ("outdated", "outdated", "incorrect"):
            self.client.post("/community/flags", json={
                "entityType": "moniker", "entityKey": "x",
                "flagType": ft, "author": "alice",
            })
        r = self.client.get("/community/flags/summary", params={
            "entityType": "moniker", "entityKey": "x",
        })
        assert r.status_code == 200
        s = r.json()
        assert s["total"] == 3
        assert s["byType"]["outdated"] == 2

    def test_update_flag_status(self):
        r = self.client.post("/community/flags", json={
            "entityType": "moniker", "entityKey": "x",
            "flagType": "outdated", "author": "alice",
        })
        flag_id = r.json()["id"]

        r = self.client.patch(f"/community/flags/{flag_id}/status", json={
            "status": "resolved", "resolvedBy": "admin",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "resolved"

    def test_create_and_get_suggestions(self):
        r = self.client.post("/community/suggestions", json={
            "entityType": "moniker", "entityKey": "x",
            "fieldName": "description", "proposedValue": "better desc",
            "author": "alice", "currentValue": "old desc", "reason": "clarity",
        })
        assert r.status_code == 201
        assert r.json()["status"] == "pending"

        r = self.client.get("/community/suggestions", params={
            "entityType": "moniker", "entityKey": "x",
        })
        assert len(r.json()) == 1

    def test_approve_suggestion(self):
        r = self.client.post("/community/suggestions", json={
            "entityType": "moniker", "entityKey": "x",
            "fieldName": "desc", "proposedValue": "new", "author": "alice",
        })
        sid = r.json()["id"]

        r = self.client.post(f"/community/suggestions/{sid}/approve", json={
            "reviewedBy": "admin", "reviewComment": "ok",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_create_and_upvote_annotation(self):
        r = self.client.post("/community/annotations", json={
            "entityType": "moniker", "entityKey": "x",
            "annotationType": "tip", "content": "Use T+1", "author": "alice",
        })
        assert r.status_code == 201
        aid = r.json()["id"]

        # Upvote
        r = self.client.post(f"/community/annotations/{aid}/upvote", json={"voter": "bob"})
        assert r.status_code == 200

        # Verify count
        r = self.client.get("/community/annotations", params={
            "entityType": "moniker", "entityKey": "x",
        })
        assert r.json()[0]["upvoteCount"] == 1

        # Remove upvote
        r = self.client.request("DELETE", f"/community/annotations/{aid}/upvote", json={"voter": "bob"})
        assert r.status_code == 200

    def test_create_discussion_and_reply(self):
        r = self.client.post("/community/discussions", json={
            "entityType": "moniker", "entityKey": "x",
            "title": "Split this?", "author": "alice",
        })
        assert r.status_code == 201
        did = r.json()["id"]
        assert r.json()["replyCount"] == 0

        # Add reply
        r = self.client.post(f"/community/discussions/{did}/replies", json={
            "content": "Yes please", "author": "bob",
        })
        assert r.status_code == 201
        assert r.json()["author"] == "bob"

        # Get detail
        r = self.client.get(f"/community/discussions/{did}")
        assert r.status_code == 200
        detail = r.json()
        assert len(detail["replies"]) == 1

    def test_helpful_votes(self):
        self.client.post("/community/helpful", json={
            "entityType": "moniker", "entityKey": "x",
            "helpful": True, "author": "alice",
        })
        self.client.post("/community/helpful", json={
            "entityType": "moniker", "entityKey": "x",
            "helpful": False, "author": "bob",
        })

        r = self.client.get("/community/helpful", params={
            "entityType": "moniker", "entityKey": "x",
        })
        assert r.status_code == 200
        s = r.json()
        assert s["helpful"] == 1
        assert s["notHelpful"] == 1
        assert s["total"] == 2

    def test_activity_summary(self):
        self.client.post("/community/flags", json={
            "entityType": "moniker", "entityKey": "x",
            "flagType": "outdated", "author": "alice",
        })
        self.client.post("/community/annotations", json={
            "entityType": "moniker", "entityKey": "x",
            "annotationType": "tip", "content": "c", "author": "alice",
        })

        r = self.client.get("/community/activity", params={
            "entityType": "moniker", "entityKey": "x",
        })
        assert r.status_code == 200
        a = r.json()
        assert a["flags"] == 1
        assert a["annotations"] == 1
        assert a["total"] == 2

    def test_auto_save_persists_to_disk(self):
        """Verify mutations are auto-saved to JSON files."""
        self.client.post("/community/flags", json={
            "entityType": "moniker", "entityKey": "persist.test",
            "flagType": "outdated", "author": "alice",
        })

        flags_path = self.tmp_path / "entities" / "moniker" / "persist.test" / "flags.json"
        assert flags_path.exists(), "Auto-save should write flags.json to disk"
        data = json.loads(flags_path.read_text(encoding="utf-8"))
        assert len(data["flags"]) == 1

    def test_404_on_nonexistent_flag(self):
        r = self.client.patch("/community/flags/nonexistent/status", json={"status": "resolved"})
        assert r.status_code == 404

    def test_404_on_nonexistent_discussion(self):
        r = self.client.get("/community/discussions/nonexistent")
        assert r.status_code == 404
