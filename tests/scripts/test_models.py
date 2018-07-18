import pytest

import leapp.models
import leapp.models.fields
from leapp.models.utils import init_from_tuple
from leapp.exceptions import ModelDefinitionError
from test_topics import UnitTestTopic


class UnitTestModel(leapp.models.Model):
    topic = UnitTestTopic
    strings = leapp.models.fields.List(leapp.models.fields.String())
    integer = leapp.models.fields.Integer()


def test_model_definition_error():
    with pytest.raises(ModelDefinitionError):
        type('FailingModelDefinition', (leapp.models.Model,), {})


def test_get_models():
    models = leapp.models.get_models()
    assert len(models) >= 2
    assert UnitTestModel in models
    assert leapp.models.ErrorModel in models


def test_init_from_tuple():
    strings_value = ['first', 'second', 'third']
    integer_value = 2
    model = init_from_tuple(UnitTestModel, ('strings', 'integer'), (strings_value, integer_value))
    assert model.strings == ['first', 'second', 'third'] and model.integer == integer_value
