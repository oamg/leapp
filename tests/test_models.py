import pytest

import leapp.models
from leapp.exceptions import ModelDefinitionError
from test_topics import UnitTestTopic


class UnitTestModel(leapp.models.Model):
    topic = UnitTestTopic


def test_model_definition_error():
    with pytest.raises(ModelDefinitionError):
        type('FailingModelDefinition', (leapp.models.Model,), {})


def test_get_models():
    models = leapp.models.get_models()
    assert len(models) >= 2
    assert UnitTestModel in models
    assert leapp.models.ErrorModel in models
