from collections import defaultdict
import pytest

from leapp.actors.config import Config, SchemaError, normalize_schemas
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
