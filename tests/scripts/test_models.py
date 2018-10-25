import pytest

import leapp.models
import leapp.models.fields
from leapp.models.utils import init_from_tuple
from leapp.exceptions import ModelDefinitionError
from test_topics import UnitTestTopic


class UnitTestModel(leapp.models.Model):
    topic = UnitTestTopic
    strings = leapp.models.fields.List(leapp.models.fields.String(), required=False)
    integer = leapp.models.fields.Integer()


class InheritedUnitTestModel(UnitTestModel):
    pass


class ExtendedInheritedUnitTestModel(InheritedUnitTestModel):
    boolean = leapp.models.fields.Boolean(default=False, required=True)


class ExtendedOverriddenInheritedUnitTestModel(ExtendedInheritedUnitTestModel):
    integer = leapp.models.fields.Number()


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


def test_inheritance():
    strings_value = ['first', 'second', 'third']
    integer_value = 2.4
    boolean_value = True
    a = ExtendedOverriddenInheritedUnitTestModel(strings=strings_value,
                                                 integer=integer_value,
                                                 boolean=boolean_value)
    assert a.boolean == boolean_value
    assert a.strings == strings_value
    assert a.integer == integer_value
    assert len(ExtendedOverriddenInheritedUnitTestModel.fields) == 3

    with pytest.raises(leapp.models.fields.ModelViolationError):
        # Ensure that passing a wrong value type will raise an exception if the field was defined in a base class
        # and overridden by a derived class. In this case  ExtendedOverriddenInheritedUnitTestModel overrides the field
        # integer to be a number, passing a number to the non overridden base class will still keep raising an exception
        ExtendedInheritedUnitTestModel(strings=strings_value, integer=integer_value, boolean=boolean_value)

    assert isinstance(ExtendedOverriddenInheritedUnitTestModel.fields['boolean'], leapp.models.fields.Boolean)
    assert isinstance(ExtendedOverriddenInheritedUnitTestModel.fields['integer'], leapp.models.fields.Number)
    assert isinstance(ExtendedOverriddenInheritedUnitTestModel.fields['strings'], leapp.models.fields.List)

    assert isinstance(ExtendedInheritedUnitTestModel.fields['boolean'], leapp.models.fields.Boolean)
    assert isinstance(ExtendedInheritedUnitTestModel.fields['integer'], leapp.models.fields.Integer)
    assert isinstance(ExtendedInheritedUnitTestModel.fields['strings'], leapp.models.fields.List)

    assert len(InheritedUnitTestModel.fields) == 2
    assert isinstance(InheritedUnitTestModel.fields['integer'], leapp.models.fields.Integer)
    assert isinstance(InheritedUnitTestModel.fields['strings'], leapp.models.fields.List)
    assert InheritedUnitTestModel.fields is not UnitTestModel.fields
