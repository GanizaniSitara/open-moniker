"""Tests for business models and applications registries.

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_models_applications.py -v
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from moniker_svc.models.types import Model, ModelOwnership, MonikerLink, FieldAlias
from moniker_svc.models.registry import ModelRegistry
from moniker_svc.models.loader import load_models_from_yaml
from moniker_svc.applications.types import Application, APPLICATION_STATUSES
from moniker_svc.applications.registry import ApplicationRegistry
from moniker_svc.applications.loader import load_applications_from_yaml


# ===================================================================
# Model types
# ===================================================================

class TestModelOwnership:
    def test_empty(self):
        o = ModelOwnership()
        assert o.is_empty()

    def test_not_empty(self):
        o = ModelOwnership(methodology_owner="quant@firm.com")
        assert not o.is_empty()

    def test_to_dict_roundtrip(self):
        o = ModelOwnership(methodology_owner="a", business_steward="b", support_channel="#c")
        d = o.to_dict()
        restored = ModelOwnership.from_dict(d)
        assert restored == o

    def test_from_dict_empty(self):
        o = ModelOwnership.from_dict({})
        assert o.is_empty()

    def test_from_dict_none(self):
        o = ModelOwnership.from_dict(None)
        assert o.is_empty()


class TestFieldAlias:
    def test_from_string(self):
        a = FieldAlias.from_dict("PVBP")
        assert a.name == "PVBP"
        assert a.type == "common_name"

    def test_from_dict(self):
        a = FieldAlias.from_dict({"name": "PVBP", "type": "abbreviation", "context": "Bloomberg"})
        assert a.name == "PVBP"
        assert a.type == "abbreviation"
        assert a.context == "Bloomberg"

    def test_to_dict_minimal(self):
        a = FieldAlias(name="DVO1")
        d = a.to_dict()
        assert d == {"name": "DVO1"}
        assert "type" not in d  # common_name is default, omitted

    def test_to_dict_full(self):
        a = FieldAlias(name="X", type="legacy_name", context="old system")
        d = a.to_dict()
        assert d["type"] == "legacy_name"
        assert d["context"] == "old system"


class TestMonikerLink:
    def test_from_string(self):
        link = MonikerLink.from_dict("risk.cvar/*/*")
        assert link.moniker_pattern == "risk.cvar/*/*"
        assert link.column_name is None

    def test_from_dict(self):
        link = MonikerLink.from_dict({
            "moniker_pattern": "risk.cvar/*/*",
            "column_name": "DV01",
            "notes": "Dollar value",
        })
        assert link.moniker_pattern == "risk.cvar/*/*"
        assert link.column_name == "DV01"
        assert link.notes == "Dollar value"

    def test_to_dict_minimal(self):
        link = MonikerLink(moniker_pattern="risk/*")
        d = link.to_dict()
        assert d == {"moniker_pattern": "risk/*"}

    def test_to_dict_full(self):
        link = MonikerLink(moniker_pattern="risk/*", column_name="DV01", notes="n")
        d = link.to_dict()
        assert "column_name" in d
        assert "notes" in d


class TestModel:
    def _make_model(self, **overrides):
        defaults = dict(
            path="risk.analytics/dv01",
            display_name="Dollar Value of 01",
            description="Change in value for 1bp yield shift",
            formula="dV/dy * 0.0001",
            unit="USD",
            appears_in=(MonikerLink(moniker_pattern="risk.cvar/*/*"),),
            semantic_tags=("risk", "sensitivity"),
        )
        defaults.update(overrides)
        return Model(**defaults)

    def test_basic_fields(self):
        m = self._make_model()
        assert m.path == "risk.analytics/dv01"
        assert m.display_name == "Dollar Value of 01"
        assert m.unit == "USD"

    def test_name_property(self):
        m = self._make_model(path="risk.analytics/dv01")
        assert m.name == "dv01"

    def test_name_no_slash(self):
        m = self._make_model(path="standalone")
        assert m.name == "standalone"

    def test_parent_path(self):
        m = self._make_model(path="risk.analytics/dv01")
        assert m.parent_path == "risk.analytics"

    def test_parent_path_root(self):
        m = self._make_model(path="toplevel")
        assert m.parent_path is None

    def test_is_container(self):
        m = self._make_model(appears_in=())
        assert m.is_container()

    def test_is_not_container(self):
        m = self._make_model()
        assert not m.is_container()

    def test_default_data_type(self):
        m = self._make_model()
        assert m.data_type == "float"

    def test_to_dict_roundtrip(self):
        m = self._make_model()
        d = m.to_dict()
        restored = Model.from_dict(d["path"], d)
        assert restored.path == m.path
        assert restored.display_name == m.display_name
        assert restored.formula == m.formula
        assert restored.unit == m.unit
        assert len(restored.appears_in) == len(m.appears_in)
        assert len(restored.semantic_tags) == len(m.semantic_tags)

    def test_from_dict_minimal(self):
        m = Model.from_dict("simple", {})
        assert m.path == "simple"
        assert m.display_name == ""
        assert m.formula is None
        assert m.appears_in == ()

    def test_from_dict_with_aliases(self):
        m = Model.from_dict("dv01", {
            "aliases": ["PVBP", {"name": "DVO1", "type": "abbreviation"}],
        })
        assert len(m.aliases) == 2
        assert m.aliases[0].name == "PVBP"
        assert m.aliases[1].type == "abbreviation"

    def test_to_dict_omits_empty(self):
        m = Model(path="x")
        d = m.to_dict()
        assert "formula" not in d
        assert "ownership" not in d
        assert "appears_in" not in d


# ===================================================================
# ModelRegistry
# ===================================================================

class TestModelRegistry:
    @pytest.fixture
    def registry(self):
        return ModelRegistry()

    def _dv01(self):
        return Model(
            path="risk.analytics/dv01",
            display_name="DV01",
            formula="dV/dy * 0.0001",
            unit="USD",
            appears_in=(MonikerLink(moniker_pattern="risk.cvar/*/*"),),
        )

    def _duration(self):
        return Model(
            path="risk.analytics/duration",
            display_name="Duration",
            unit="years",
            appears_in=(MonikerLink(moniker_pattern="risk.cvar/*/*"),),
        )

    def _container(self):
        return Model(path="risk.analytics", display_name="Risk Analytics")

    def test_register_and_get(self, registry):
        registry.register(self._dv01())
        m = registry.get("risk.analytics/dv01")
        assert m is not None
        assert m.display_name == "DV01"

    def test_get_nonexistent(self, registry):
        assert registry.get("nope") is None

    def test_get_or_raise(self, registry):
        registry.register(self._dv01())
        m = registry.get_or_raise("risk.analytics/dv01")
        assert m.display_name == "DV01"

    def test_get_or_raise_missing(self, registry):
        with pytest.raises(KeyError):
            registry.get_or_raise("nope")

    def test_exists(self, registry):
        registry.register(self._dv01())
        assert registry.exists("risk.analytics/dv01")
        assert not registry.exists("nope")

    def test_duplicate_raises(self, registry):
        registry.register(self._dv01())
        with pytest.raises(ValueError, match="already registered"):
            registry.register(self._dv01())

    def test_register_or_update(self, registry):
        registry.register(self._dv01())
        updated = Model(path="risk.analytics/dv01", display_name="Updated DV01")
        registry.register_or_update(updated)
        assert registry.get("risk.analytics/dv01").display_name == "Updated DV01"

    def test_delete(self, registry):
        registry.register(self._dv01())
        assert registry.delete("risk.analytics/dv01") is True
        assert registry.get("risk.analytics/dv01") is None

    def test_delete_nonexistent(self, registry):
        assert registry.delete("nope") is False

    def test_clear(self, registry):
        registry.register(self._dv01())
        registry.register(self._duration())
        registry.clear()
        assert registry.count() == 0

    def test_count(self, registry):
        assert registry.count() == 0
        registry.register(self._dv01())
        assert registry.count() == 1

    def test_all_models(self, registry):
        registry.register(self._dv01())
        registry.register(self._duration())
        models = registry.all_models()
        assert len(models) == 2
        assert models[0].path < models[1].path  # sorted

    def test_all_paths(self, registry):
        registry.register(self._dv01())
        registry.register(self._duration())
        paths = registry.all_paths()
        assert paths == ["risk.analytics/duration", "risk.analytics/dv01"]

    def test_dunder_len(self, registry):
        registry.register(self._dv01())
        assert len(registry) == 1

    def test_dunder_contains(self, registry):
        registry.register(self._dv01())
        assert "risk.analytics/dv01" in registry
        assert "nope" not in registry

    def test_dunder_getitem(self, registry):
        registry.register(self._dv01())
        m = registry["risk.analytics/dv01"]
        assert m.display_name == "DV01"

    def test_dunder_iter(self, registry):
        registry.register(self._dv01())
        registry.register(self._duration())
        models = list(registry)
        assert len(models) == 2


class TestModelRegistryHierarchy:
    @pytest.fixture
    def registry(self):
        reg = ModelRegistry()
        reg.register(Model(path="risk.analytics", display_name="Risk Analytics"))
        reg.register(Model(path="risk.analytics/dv01", display_name="DV01"))
        reg.register(Model(path="risk.analytics/duration", display_name="Duration"))
        reg.register(Model(path="performance", display_name="Performance"))
        return reg

    def test_children_paths(self, registry):
        children = registry.children_paths("risk.analytics")
        assert "risk.analytics/dv01" in children
        assert "risk.analytics/duration" in children

    def test_children_paths_root(self, registry):
        roots = registry.children_paths("")
        assert "risk.analytics" in roots
        assert "performance" in roots
        assert "risk.analytics/dv01" not in roots

    def test_children(self, registry):
        children = registry.children("risk.analytics")
        assert len(children) == 2

    def test_build_tree(self, registry):
        tree = registry.build_tree()
        assert "risk.analytics" in tree


class TestModelRegistryMonikerLookup:
    @pytest.fixture
    def registry(self):
        reg = ModelRegistry()
        reg.register(Model(
            path="risk.analytics/dv01",
            appears_in=(MonikerLink(moniker_pattern="risk.cvar/*/*"),),
        ))
        reg.register(Model(
            path="risk.analytics/duration",
            appears_in=(MonikerLink(moniker_pattern="risk.cvar/*/*"),),
        ))
        reg.register(Model(
            path="perf/alpha",
            appears_in=(MonikerLink(moniker_pattern="portfolios/*/returns"),),
        ))
        return reg

    def test_models_for_moniker_match(self, registry):
        models = registry.models_for_moniker("risk.cvar/port-1/USD")
        paths = [m.path for m in models]
        assert "risk.analytics/dv01" in paths
        assert "risk.analytics/duration" in paths

    def test_models_for_moniker_no_match(self, registry):
        models = registry.models_for_moniker("unrelated/path")
        assert models == []

    def test_models_for_moniker_different_pattern(self, registry):
        models = registry.models_for_moniker("portfolios/fund-a/returns")
        assert len(models) == 1
        assert models[0].path == "perf/alpha"

    def test_monikers_for_model(self, registry):
        patterns = registry.monikers_for_model("risk.analytics/dv01")
        assert "risk.cvar/*/*" in patterns

    def test_monikers_for_model_not_found(self, registry):
        assert registry.monikers_for_model("nope") == []


# ===================================================================
# Model YAML loader
# ===================================================================

class TestModelLoader:
    def test_load_from_yaml(self, tmp_path):
        yaml_content = {
            "risk.analytics/dv01": {
                "display_name": "DV01",
                "formula": "dV/dy * 0.0001",
                "unit": "USD",
                "appears_in": [{"moniker_pattern": "risk.cvar/*/*"}],
            },
            "risk.analytics/duration": {
                "display_name": "Duration",
                "unit": "years",
            },
        }
        f = tmp_path / "models.yaml"
        f.write_text(yaml.dump(yaml_content), encoding="utf-8")

        models = load_models_from_yaml(f)
        assert len(models) == 2

    def test_load_into_registry(self, tmp_path):
        yaml_content = {
            "test/model": {"display_name": "Test"},
        }
        f = tmp_path / "models.yaml"
        f.write_text(yaml.dump(yaml_content), encoding="utf-8")

        reg = ModelRegistry()
        load_models_from_yaml(f, reg)
        assert reg.count() == 1
        assert reg.get("test/model").display_name == "Test"

    def test_load_missing_file(self):
        models = load_models_from_yaml("/nonexistent/models.yaml")
        assert models == []

    def test_load_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        models = load_models_from_yaml(f)
        assert models == []

    def test_load_sample_models_yaml(self):
        sample = _REPO_ROOT / "sample_models.yaml"
        if sample.exists():
            reg = ModelRegistry()
            models = load_models_from_yaml(sample, reg)
            assert len(models) > 0
            assert reg.count() == len(models)


# ===================================================================
# Application types
# ===================================================================

class TestApplication:
    def test_from_dict_minimal(self):
        app = Application.from_dict("myapp", {})
        assert app.key == "myapp"
        assert app.display_name == "myapp"  # defaults to key
        assert app.status == "active"
        assert app.datasets == []
        assert app.fields == []

    def test_from_dict_full(self):
        app = Application.from_dict("murex", {
            "display_name": "Murex",
            "description": "Trading platform",
            "category": "Trading",
            "color": "#8E44AD",
            "status": "active",
            "owner": "trading@firm.com",
            "tech_lead": "dev@firm.com",
            "support_channel": "#murex-support",
            "datasets": ["risk.cvar/*", "portfolios/*"],
            "fields": ["risk.analytics/dv01"],
            "documentation_url": "https://wiki/murex",
        })
        assert app.display_name == "Murex"
        assert app.category == "Trading"
        assert len(app.datasets) == 2
        assert len(app.fields) == 1

    def test_to_dict_roundtrip(self):
        app = Application.from_dict("test", {
            "display_name": "Test App",
            "datasets": ["data/*"],
        })
        d = app.to_dict()
        assert d["key"] == "test"
        assert d["display_name"] == "Test App"
        assert d["datasets"] == ["data/*"]

    def test_valid_statuses(self):
        assert "active" in APPLICATION_STATUSES
        assert "planned" in APPLICATION_STATUSES
        assert "decommissioned" in APPLICATION_STATUSES


# ===================================================================
# ApplicationRegistry
# ===================================================================

class TestApplicationRegistry:
    @pytest.fixture
    def registry(self):
        return ApplicationRegistry()

    def _murex(self):
        return Application(key="murex", display_name="Murex", datasets=["risk.cvar/*"])

    def _calypso(self):
        return Application(key="calypso", display_name="Calypso", fields=["risk.analytics/dv01"])

    def test_register_and_get(self, registry):
        registry.register(self._murex())
        app = registry.get("murex")
        assert app is not None
        assert app.display_name == "Murex"

    def test_get_nonexistent(self, registry):
        assert registry.get("nope") is None

    def test_get_or_raise(self, registry):
        registry.register(self._murex())
        app = registry.get_or_raise("murex")
        assert app.key == "murex"

    def test_get_or_raise_missing(self, registry):
        with pytest.raises(KeyError):
            registry.get_or_raise("nope")

    def test_duplicate_raises(self, registry):
        registry.register(self._murex())
        with pytest.raises(ValueError, match="already registered"):
            registry.register(self._murex())

    def test_register_or_update(self, registry):
        registry.register(self._murex())
        updated = Application(key="murex", display_name="Murex v2")
        registry.register_or_update(updated)
        assert registry.get("murex").display_name == "Murex v2"

    def test_exists(self, registry):
        registry.register(self._murex())
        assert registry.exists("murex")
        assert not registry.exists("nope")

    def test_delete(self, registry):
        registry.register(self._murex())
        assert registry.delete("murex") is True
        assert registry.get("murex") is None

    def test_delete_nonexistent(self, registry):
        assert registry.delete("nope") is False

    def test_clear(self, registry):
        registry.register(self._murex())
        registry.register(self._calypso())
        registry.clear()
        assert registry.count() == 0

    def test_count(self, registry):
        assert registry.count() == 0
        registry.register(self._murex())
        assert registry.count() == 1

    def test_all_applications(self, registry):
        registry.register(self._murex())
        registry.register(self._calypso())
        apps = registry.all_applications()
        assert len(apps) == 2
        assert apps[0].key < apps[1].key  # sorted

    def test_application_keys(self, registry):
        registry.register(self._murex())
        registry.register(self._calypso())
        assert registry.application_keys() == ["calypso", "murex"]

    def test_dunder_len(self, registry):
        registry.register(self._murex())
        assert len(registry) == 1

    def test_dunder_contains(self, registry):
        registry.register(self._murex())
        assert "murex" in registry

    def test_dunder_iter(self, registry):
        registry.register(self._murex())
        apps = list(registry)
        assert len(apps) == 1


class TestApplicationRegistryLookup:
    @pytest.fixture
    def registry(self):
        reg = ApplicationRegistry()
        reg.register(Application(
            key="murex", datasets=["risk.cvar/*", "portfolios/*"],
            fields=["risk.analytics/dv01"],
        ))
        reg.register(Application(
            key="calypso", datasets=["credit.*"],
            fields=["risk.analytics/duration"],
        ))
        return reg

    def test_find_by_dataset_match(self, registry):
        apps = registry.find_by_dataset("risk.cvar/port-1")
        assert len(apps) == 1
        assert apps[0].key == "murex"

    def test_find_by_dataset_no_match(self, registry):
        apps = registry.find_by_dataset("unrelated/data")
        assert apps == []

    def test_find_by_field_match(self, registry):
        apps = registry.find_by_field("risk.analytics/dv01")
        assert len(apps) == 1
        assert apps[0].key == "murex"

    def test_find_by_field_no_match(self, registry):
        apps = registry.find_by_field("nope")
        assert apps == []


# ===================================================================
# Application YAML loader
# ===================================================================

class TestApplicationLoader:
    def test_load_from_yaml(self, tmp_path):
        yaml_content = {
            "murex": {
                "display_name": "Murex",
                "category": "Trading",
                "datasets": ["risk.cvar/*"],
            },
            "calypso": {
                "display_name": "Calypso",
            },
        }
        f = tmp_path / "apps.yaml"
        f.write_text(yaml.dump(yaml_content), encoding="utf-8")

        apps = load_applications_from_yaml(f)
        assert len(apps) == 2

    def test_load_into_registry(self, tmp_path):
        yaml_content = {"testapp": {"display_name": "Test"}}
        f = tmp_path / "apps.yaml"
        f.write_text(yaml.dump(yaml_content), encoding="utf-8")

        reg = ApplicationRegistry()
        load_applications_from_yaml(f, reg)
        assert reg.count() == 1

    def test_load_missing_file(self):
        apps = load_applications_from_yaml("/nonexistent/apps.yaml")
        assert apps == []

    def test_load_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        apps = load_applications_from_yaml(f)
        assert apps == []

    def test_load_sample_applications_yaml(self):
        sample = _REPO_ROOT / "sample_applications.yaml"
        if sample.exists():
            reg = ApplicationRegistry()
            apps = load_applications_from_yaml(sample, reg)
            assert len(apps) > 0
