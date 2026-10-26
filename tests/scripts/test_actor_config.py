from collections import defaultdict
from unittest import  mock

import pytest

from leapp.actors.config import Config, SchemaError, _warn_about_unknown_config, normalize_schemas
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


def _warnings(actor_config):
    schema = normalize_schemas([(_TestConfigA, _TestConfigB)])
    with mock.patch('leapp.actors.config.log') as log_mock:
        _warn_about_unknown_config(actor_config, schema)
    return [args[0] for args, _kwargs in log_mock.warning.call_args_list]


def test_warn_about_unknown_config_valid():
    """A config matching the schema produces no warnings."""
    actor_config = {
        "test": {"a_setting": "value"},
        "other_section": {"other_setting": "value"},
    }
    assert _warnings(actor_config) == []


def test_warn_about_unknown_config_unknown_section():
    """
    An unknown section is reported.
    """
    actor_config = {"bogus_section": {"a_setting": "value"}}
    warnings = _warnings(actor_config)
    assert any(
        "A config file contained an unknown section:" in w and "bogus_section" in w
        for w in warnings
    )


def test_warn_about_unknown_config_unknown_field():
    """
    An unknown field within a known section is reported.
    """
    actor_config = {"test": {"a_setting": "value", "bogus_field": "value"}}
    warnings = _warnings(actor_config)
    assert any(
        "A config file contained an unknown field:" in w and "bogus_field" in w
        for w in warnings
    )


def test_warn_about_unknown_config_known_field_no_warning():
    """
    A known field within a known section is not reported as unknown.
    """
    actor_config = {"test": {"a_setting": "value"}}
    warnings = _warnings(actor_config)
    assert not any("unknown field" in w for w in warnings)


def test_warn_about_unknown_config_reserved_field():
    """
    Reserved fields ending in '__' are not reported as unknown.
    """
    actor_config = {"test": {"a_setting": "value", "a_setting__": "docs"}}
    warnings = _warnings(actor_config)
    assert not any("unknown field" in w for w in warnings)
