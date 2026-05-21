from collections import defaultdict
import pytest

from leapp.actors import config as config_module
from leapp.actors.config import (
    Config,
    ConfigDefinitionError,
    SchemaError,
    normalize_schemas,
    retrieve_config,
)
from leapp.models import fields


class _TestConfigA(Config):
    section = "test"
    name = "a_setting"
    type_ = fields.String()
    description = 'Description here'
    default = "default value"


class _TestConfigB(Config):
    section = "other_section"
    name = "other_setting"
    type_ = fields.String()
    description = 'Description here'
    default = "some default value"


# conflicts in default
class _TestConfigConflictsInDefault(Config):
    section = "test"
    name = "a_setting"
    type_ = fields.String()
    description = 'Description here'
    default = "different than in A"


# conflicts in type_
class _TestConfigConflictsInType(Config):
    section = "test"
    name = "a_setting"
    type_ = fields.Integer()
    description = 'Description here'
    default = "default value"


@pytest.mark.parametrize(
    "schemas",
    [
        # test configs from single actors are merged
        [(_TestConfigA, _TestConfigB)],
        # test configs from multiple actors are merged
        [(_TestConfigA,), (_TestConfigB,)],
        # test "deduplication"
        [(_TestConfigA, _TestConfigA, _TestConfigB)],
        [(_TestConfigA,), (_TestConfigA, _TestConfigB,)]
    ],
)
def test_normalize_schemas_ok(schemas):
    """
    Test that valid schemas are detected and if required deduplicated
    """
    expect = defaultdict(dict)
    expect["test"] = {"a_setting": _TestConfigA}
    expect["other_section"] = {"other_setting": _TestConfigB}
    ret = normalize_schemas(schemas)
    assert ret == expect


def test_normalize_schemas_identical():
    """
    Test that identical Config class objects are deduplicated
    """
    expect = defaultdict(dict)
    expect["test"] = {"a_setting": _TestConfigA}

    config = _TestConfigA

    schemas = [(config, config)]
    ret = normalize_schemas(schemas)
    assert ret == expect

    schemas = [(config,), (config,)]
    ret = normalize_schemas(schemas)
    assert ret == expect


@pytest.mark.parametrize(
    "schemas",
    [
        [(_TestConfigA, _TestConfigConflictsInDefault)],
        [(_TestConfigA, _TestConfigConflictsInType)],
    ]
)
def test_normalize_schemas_intra_conflict(schemas):
    """
    Test that conflicts within a single Actor config schema are detected
    """
    with pytest.raises(SchemaError):
        normalize_schemas(schemas)


@pytest.mark.parametrize(
    "schemas",
    [
        [(_TestConfigA,), (_TestConfigConflictsInDefault,)],
        [(_TestConfigA,), (_TestConfigConflictsInType,)],
    ]
)
def test_normalize_schemas_inter_conflict(schemas):
    """
    Test that conflicts between multiple Actor config schemas are detected
    """
    with pytest.raises(SchemaError):
        normalize_schemas(schemas)


def test_normalize_schemas_empty():
    assert normalize_schemas([]) == defaultdict(dict)


def _make_config(attrs, cls_name="_DynamicConfig"):
    """
    Build a Config subclass with the given class attributes.

    Using ``type()`` triggers ``Config.__init_subclass__`` (and thus the
    definition-time validation) just like a normal ``class`` statement would.
    """
    return type(cls_name, (Config,), attrs)


def _valid_attrs():
    return {
        "section": "test",
        "name": "a_setting",
        "type_": fields.String(),
        "description": "Description here",
        "default": "default value",
    }


def test_config_subclass_valid_definition():
    """
    A subclass that overrides every field with valid values is accepted.
    """
    cfg = _make_config(_valid_attrs())
    assert cfg.section == "test"
    assert cfg.name == "a_setting"


def test_config_subclass_cannot_be_instantiated():
    """
    Config subclasses act as schema definitions and must not be instantiated.
    """
    with pytest.raises(TypeError):
        _TestConfigA()


def test_config_base_class_cannot_be_instantiated():
    """
    The Config base class itself must not be instantiated either.
    """
    with pytest.raises(TypeError):
        Config()


@pytest.mark.parametrize(
    "missing_field",
    ["section", "name", "description", "type_", "default"],
)
def test_config_subclass_missing_field(missing_field):
    """
    Every required field must be explicitly overridden by the subclass.
    """
    attrs = _valid_attrs()
    del attrs[missing_field]
    with pytest.raises(ConfigDefinitionError):
        _make_config(attrs)


@pytest.mark.parametrize(
    "null_field",
    ["section", "name", "description", "type_", "default"],
)
def test_config_subclass_none_field(null_field):
    """
    A required field explicitly overridden with None is rejected.
    """
    attrs = _valid_attrs()
    attrs[null_field] = None
    with pytest.raises(ConfigDefinitionError):
        _make_config(attrs)


@pytest.mark.parametrize(
    "type_value",
    [
        "not a field",
        fields.String,  # the class, not an instance
    ],
)
def test_config_subclass_invalid_type_(type_value):
    """
    type_ must be an instance of a *subclass* of leapp.models.fields.Field.
    """
    attrs = _valid_attrs()
    attrs["type_"] = type_value
    with pytest.raises(ConfigDefinitionError):
        _make_config(attrs)


def test_config_subclass_type_with_default():
    """
    The Field passed as type_ must not carry its own default; the 'default'
    class variable is used instead.
    """
    attrs = _valid_attrs()
    attrs["type_"] = fields.String(default="field default")
    with pytest.raises(ConfigDefinitionError):
        _make_config(attrs)


def test_retrieve_config(monkeypatch):
    """
    retrieve_config picks the values of the given schema out of the loaded
    actor configuration, grouped by section and name.
    """
    loaded = {
        "test": {"a_setting": "value a"},
        "other_section": {"other_setting": "value b"},
    }
    monkeypatch.setattr(config_module, "_ACTOR_CONFIG", loaded)

    result = retrieve_config((_TestConfigA, _TestConfigB))
    assert result == {
        "test": {"a_setting": "value a"},
        "other_section": {"other_setting": "value b"},
    }


def test_retrieve_config_subset():
    """
    retrieve_config only returns the fields requested in the schema.
    """
    config_module._ACTOR_CONFIG = {
        "test": {"a_setting": "value a"},
        "other_section": {"other_setting": "value b"},
    }
    try:
        result = retrieve_config((_TestConfigA,))
        assert result == {"test": {"a_setting": "value a"}}
    finally:
        config_module._ACTOR_CONFIG = None
