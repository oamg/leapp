import json
from datetime import datetime

import pytest
import six

from leapp.models import Model, fields
from leapp.topics import Topic


class BadBuiltinField(fields.BuiltinField):
    pass


class ModelTestTopic(Topic):
    name = 'model-test-topic'


class BasicModel(Model):
    topic = ModelTestTopic
    message = fields.String(required=True, default='Default Value')


class WithStringListModel(Model):
    topic = ModelTestTopic
    messages = fields.List(fields.String(), required=True)


class WithNestedModel(Model):
    topic = ModelTestTopic
    basic = fields.Nested(BasicModel, required=False, allow_null=True)


class WithRequiredNestedModel(Model):
    topic = ModelTestTopic
    basic = fields.Nested(BasicModel, required=True)


class WithNestedListModel(Model):
    topic = ModelTestTopic
    items = fields.List(fields.Nested(BasicModel), required=False)


class AllFieldTypesModel(Model):
    topic = ModelTestTopic
    float_field = fields.Float(default=3.14, required=True)
    number_int_field = fields.Number(default=1.2, required=True)
    number_float_field = fields.Number(default=2, required=True)
    integer_field = fields.Integer(default=1, required=True)
    str_field = fields.String(default='string', required=True)
    unicode_field = fields.String(default=u'Unicode string', required=True)
    date_field = fields.DateTime(default=datetime.utcnow(), required=True)
    bool_field = fields.Boolean(default=True, required=True)


class RequiredFieldModel(Model):
    topic = ModelTestTopic
    field = fields.String(required=True)


def test_builtin_needs_override():
    with pytest.raises(NotImplementedError):
        BadBuiltinField(allow_null=True, required=False).to_builtin(None, '', None)


def test_base_usage():
    with pytest.raises(fields.ModelMisuseError):
        fields.Field()


def test_basic_model():
    m = BasicModel(message='Some message')
    m2 = BasicModel.create(m.dump())
    assert m.message == m2.message


def test_string_list_model():
    m = WithStringListModel(messages=['Some message'])
    m2 = WithStringListModel.create(m.dump())
    assert m.messages == m2.messages
    m2.messages = 'str'

    with pytest.raises(fields.ModelViolationError):
        m2.dump()

    with pytest.raises(fields.ModelViolationError):
        WithStringListModel(messages='str')


def test_string_fields_violations():
    f = fields.String()
    with pytest.raises(fields.ModelViolationError):
        f._validate_model_value(1, 'test_value')

    with pytest.raises(fields.ModelViolationError):
        f._validate_builtin_value(1, 'test_value')


def test_nested_model():
    m = WithNestedModel(basic=BasicModel(message='Some message'))
    m2 = WithNestedModel.create(m.dump())
    assert m.basic == m2.basic

    with pytest.raises(fields.ModelMisuseError):
        fields.Nested(fields.String())

    with pytest.raises(fields.ModelMisuseError):
        fields.Nested(fields.String)

    with pytest.raises(fields.ModelViolationError):
        WithNestedModel(basic='Some message')

    m = WithNestedModel()
    m.basic = None
    m.dump()

    with pytest.raises(fields.ModelViolationError):
        x = WithRequiredNestedModel(basic=BasicModel(message='Some message'))
        x.basic = None
        x.dump()

    with pytest.raises(fields.ModelViolationError):
        WithRequiredNestedModel.create(dict(basic=None))

    with pytest.raises(fields.ModelViolationError):
        WithRequiredNestedModel(basic=None)

    assert WithRequiredNestedModel.create({'basic': {'message': 'test-message'}}).basic.message == 'test-message'
    assert WithRequiredNestedModel(basic=BasicModel(message='test-message')).basic.message == 'test-message'


def test_nested_list_model():
    m = WithNestedListModel(items=[BasicModel(message='Some message')])
    m2 = WithNestedListModel.create(m.dump())
    assert m.items == m2.items


def test_field_types():
    m = AllFieldTypesModel()
    m2 = AllFieldTypesModel.create(m.dump())
    assert m == m2


def test_misuse_wrong_list_element_parameter():
    with pytest.raises(fields.ModelMisuseError):
        class RaisesNonFieldType(Model):
            topic = ModelTestTopic
            boo = fields.List('')

    with pytest.raises(fields.ModelMisuseError):
        class RaisesNonFieldInstance(Model):
            topic = ModelTestTopic
            boo = fields.List(str)

    with pytest.raises(fields.ModelMisuseError):
        class RaisesNonInstance(Model):
            topic = ModelTestTopic
            boo = fields.List(fields.String)


def test_list_field():
    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.String(), required=True, allow_null=False)._validate_builtin_value('something', 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.String(), required=True, allow_null=False)._convert_to_model(None, 'test-value')

    fields.List(fields.String(), required=True, allow_null=True)._convert_to_model(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.String(), required=True, allow_null=False)._convert_from_model(None, 'test-value')

    fields.List(fields.String(), required=True, allow_null=True)._convert_from_model(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.Integer(), minimum=1)._validate_builtin_value([], 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.Integer(), minimum=1)._validate_model_value([], 'test-value')

    fields.List(fields.Integer(), minimum=1)._validate_builtin_value([1], 'test-value')
    fields.List(fields.Integer(), minimum=1)._validate_builtin_value([1, 2], 'test-value')
    fields.List(fields.Integer(), minimum=1)._validate_model_value([1], 'test-value')
    fields.List(fields.Integer(), minimum=1)._validate_model_value([1, 2], 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.Integer(), minimum=1, maximum=1)._validate_builtin_value([1, 2], 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.Integer(), minimum=1, maximum=1)._validate_model_value([1, 2], 'test-value')

    fields.List(fields.Integer(), maximum=2)._validate_builtin_value([1], 'test-value')
    fields.List(fields.Integer(), maximum=2)._validate_builtin_value([1, 2], 'test-value')

    fields.List(fields.Integer(), maximum=2)._validate_model_value([1], 'test-value')
    fields.List(fields.Integer(), maximum=2)._validate_model_value([1, 2], 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.List(fields.Integer(), maximum=3)._validate_builtin_value([1, 2, 3, 4], 'test-value')


def test_datetime_field():
    with pytest.raises(fields.ModelViolationError):
        fields.DateTime()._convert_to_model('something', 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.DateTime(required=True, allow_null=False)._convert_to_model(None, 'test-value')

    fields.DateTime(required=True, allow_null=True)._convert_to_model(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.DateTime(required=True, allow_null=False)._convert_from_model(None, 'test-value')

    fields.DateTime(required=True, allow_null=True)._convert_from_model(None, 'test-value')


def test_nested_field():
    with pytest.raises(fields.ModelViolationError):
        fields.Nested(BasicModel, allow_null=False)._convert_to_model('something', 'test-value')
    with pytest.raises(fields.ModelViolationError):
        fields.Nested(BasicModel, allow_null=False)._convert_to_model(None, 'test-value')
    fields.Nested(BasicModel, allow_null=True)._convert_to_model(None, 'test-value')


def test_required_field_types():
    with pytest.raises(fields.ModelViolationError):
        m = RequiredFieldModel(field='str')
        m.field = None
        m.dump()

    with pytest.raises(fields.ModelViolationError):
        RequiredFieldModel()

    RequiredFieldModel(field='str')

    # Don't allow null
    with pytest.raises(fields.ModelViolationError):
        fields.String(required=True, allow_null=False)._validate_model_value(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.String(required=False, allow_null=False)._validate_model_value(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.String(required=True, allow_null=False)._validate_builtin_value(None, 'test-value')

    with pytest.raises(fields.ModelViolationError):
        fields.String(required=False, allow_null=False)._validate_builtin_value(None, 'test-value')

    # Allow null
    fields.String(required=True, allow_null=True)._validate_model_value(None, 'test-value')
    fields.String(required=False, allow_null=True)._validate_model_value(None, 'test-value')
    fields.String(required=True, allow_null=True)._validate_builtin_value(None, 'test-value')
    fields.String(required=False, allow_null=True)._validate_builtin_value(None, 'test-value')


def _make_object(instance, value):
    def init(self):
        setattr(self, instance.name, value)

    return type('Dynamic' + instance.field_type.__name__, (object,), {'__init__': init})()


def _make_dict(instance, value):
    return {instance.name: value}


def create_fixture(field, value, name):
    def init(self):
        setattr(self, 'field_type', field)

    return type('Fixture', (object,), {
        'value': value,
        'name': name,
        'make_object': _make_object,
        'make_dict': _make_dict,
        '__init__': init
    })()


def _create_field_string_list(**kwargs):
    return fields.List(fields.String(), **kwargs)


def _create_nested_base_model_field(**kwargs):
    return fields.Nested(BasicModel, **kwargs)


BASIC_TYPE_FIXTURES = (
    create_fixture(fields.String, 'Test String Value', 'string_value'),
    create_fixture(fields.Boolean, True, 'boolean_value'),
    create_fixture(fields.Integer, 1, 'integer_value'),
    create_fixture(fields.Float, 3.14, 'float_value'),
    create_fixture(fields.Number, 3.14, 'number_float_value'),
    create_fixture(fields.Number, 2, 'number_integer_value'),
    create_fixture(fields.DateTime, datetime.utcnow(), 'datetime_value'),
    create_fixture(_create_field_string_list, ['a', 'b', 'c'], 'string_list_value'),
    create_fixture(_create_nested_base_model_field, BasicModel(message='Test message'), 'nested_model_value')
)


@pytest.mark.parametrize("case", BASIC_TYPE_FIXTURES)
def test_basic_types_sanity(case):
    source = case.make_object(case.value)
    target = {}
    case.field_type(required=True, allow_null=False).to_builtin(source, case.name, target)
    json.dumps(target)

    with pytest.raises(fields.ModelViolationError):
        source = case.make_object(fields.missing)
        target = {}
        # Should raise an exception because the value missing is not valid
        case.field_type(required=True, default=None, allow_null=True).to_builtin(source, case.name, target)

    with pytest.raises(fields.ModelViolationError):
        source = case.make_object(fields.missing)
        target = {}
        # Should raise an exception because the value missing is not valid and required=True
        case.field_type(required=True).to_builtin(source, case.name, target)

    source = case.make_object(None)
    target = {}
    case.field_type(required=True, allow_null=True).to_builtin(source, case.name, target)
    assert case.name in target and target[case.name] is None

    with pytest.raises(fields.ModelViolationError):
        source = case.make_object(None)
        target = {}
        # Should raise an exception because the field is required and null is not allowed
        case.field_type(required=True, allow_null=False).to_builtin(source, case.name, target)

    with pytest.raises(fields.ModelViolationError):
        source = case.make_object(None)
        target = {}
        # Should raise an exception because the field null is not allowed
        case.field_type(required=False, allow_null=False).to_builtin(source, case.name, target)

    source = case.make_object(fields.missing)
    target = {}
    case.field_type(required=False, allow_null=False).to_builtin(source, case.name, target)
    assert case.name not in target
    json.dumps(target)

    source = case.make_object(case.value)
    target = {}
    field = case.field_type(required=False, allow_null=False)
    field.to_builtin(source, case.name, target)
    assert target.get(case.name) == field._convert_from_model(case.value, case.name)
    json.dumps(target)

    source = case.make_object(None)
    target = {}
    field = case.field_type(required=False, allow_null=True)
    field.to_builtin(source, case.name, target)
    assert target.get(case.name) is None
    json.dumps(target)

    assert isinstance(field.help, six.string_types)
