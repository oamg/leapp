import pytest

import leapp.messaging.answerstore
from leapp.messaging.answerstore import AnswerStore, multiprocessing, _comment_out


class MockManager(object):
    def __call__(self):
        return self

    @staticmethod
    def dict(*args):
        return dict(*args)


class MockComponentKey1(object):
    value_type = str
    key = 'key1'
    label = 'label key1'
    description = 'description key1'
    reason = 'Unbelievable reason'
    default = False
    value = None


class MockComponentKey2(object):
    value_type = str
    key = 'key2'
    label = 'label key2'
    description = 'description key2'
    reason = 'Cannot reason with this reason'
    default = 'Default'
    value = None


class MockComponentKey1Bool(object):
    value_type = bool
    key = 'key1'
    label = 'label bool key1'
    description = 'description bool key1'
    reason = 'Unreasonable Reason'
    default = True
    value = None


class MockComponentKey2Bool(object):
    value_type = bool
    key = 'key2'
    label = 'label bool key2'
    description = 'description bool key2'
    reason = 'Unbearable\nReason\nxxx'
    default = False
    value = None


class MockComponentTextListKey1(object):
    value_type = list
    key = 'key1'
    label = 'label key1'
    description = 'description key1'
    reason = 'Unbelievable reason'
    default = None
    value = None


class MockComponentTextListKey2(object):
    value_type = list
    key = 'key2'
    label = 'label key2'
    description = 'description key2'
    reason = 'Unbelievable reason'
    default = None
    value = None


class MockDialogScope1(object):
    scope = 'scope1'
    title = 'Mock Dialog scope1'
    reason = 'Mock Test Data for scope1'
    components = (MockComponentKey1, MockComponentKey2)


class MockDialogScope2(object):
    scope = 'scope2'
    title = 'Mock Dialog scope2'
    reason = 'Mock Test Data for scope2'
    components = (MockComponentKey1, MockComponentKey2)


class MockDialogBoolScope(object):
    scope = 'boolscope'
    title = 'Mock Dialog boolscope'
    reason = 'Mock Test Data for boolscope'
    components = (MockComponentKey1Bool, MockComponentKey2Bool)


class MockDialogTextListScope(object):
    scope = 'textlistscope'
    title = 'Mock Dialog textlistscope'
    reason = 'Mock Test Data for textlistscope'
    components = (MockComponentTextListKey1, MockComponentTextListKey2)


class MockWorkflow(object):
    dialogs = (MockDialogScope1, MockDialogScope2, MockDialogBoolScope, MockDialogTextListScope)


@pytest.fixture(scope='function')
def answerfile_data():
    yield '''
[scope1]
key1=scope1.key1
key2=scope1.key2

[scope2]
key1=scope2.key1
key2=scope2.key2

[boolscope]
key1=True
Key2=False

[textlistscope]
key1= [
  "key1.value1",
  "key1.value2"
  ]
key2=["key2.value1", "key2.value2"]
    '''


@pytest.fixture(scope='function', name='answerfile')
def answerfile_file(tmpdir, answerfile_data):
    d = tmpdir.join('answerfile')
    d.mkdir()
    f = d.join('data.ini')
    f.write(answerfile_data)
    yield str(f)


def test_answerstore_init(monkeypatch):
    manager = MockManager()
    assert type(AnswerStore()._storage) is multiprocessing.managers.DictProxy
    monkeypatch.setattr(multiprocessing, 'Manager', MockManager())
    assert type(AnswerStore(manager=manager)._storage) is dict
    assert type(AnswerStore()._storage) is dict


def test_answerstore_answer():
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.answer(scope='scope1', key='key1', value='scope1.key1')
    a.answer(scope='scope1', key='key2', value='scope1.key2')
    a.answer(scope='scope2', key='key1', value='scope2.key1')
    a.answer(scope='scope2', key='key2', value='scope2.key2')
    a.answer(scope='textlistscope', key='key1', value=['key1.value1', 'key1.value2'])
    assert 'scope1' in store.keys()
    assert 'scope2' in store.keys()
    assert 'textlistscope' in store.keys()
    assert 'key1' in store['scope1'].keys()
    assert 'key1' in store['scope1'].keys()
    assert 'key1' in store['textlistscope'].keys()
    assert 'key1' in store['scope2']
    assert 'key2' in store['scope2']
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['textlistscope']['key1'] == ['key1.value1', 'key1.value2']


def test_answerstore_update(answerfile, answerfile_data, tmpdir):
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load(answerfile)
    assert store['boolscope']['key1'] == 'True'
    assert store['boolscope']['key2'] == 'False'
    assert store['textlistscope']['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    assert store['textlistscope']['key2'] == '["key2.value1", "key2.value2"]'
    a.answer('boolscope', 'key1', False)
    a.answer('boolscope', 'key2', True)
    a.answer('textlistscope', 'key1', ['key1.value1', 'key1.value2'])
    a.answer('textlistscope', 'key2', ['key2.value1', 'key2.value2'])
    assert store['boolscope']['key1'] is False
    assert store['boolscope']['key2'] is True
    assert store['textlistscope']['key1'] == ['key1.value1', 'key1.value2']
    assert store['textlistscope']['key2'] == ['key2.value1', 'key2.value2']
    f = tmpdir.join('test_answerstore_update')
    f.write(answerfile_data)
    a.update(str(f))
    a2 = AnswerStore(manager=m)
    store2 = a2._storage
    a2.load(str(f))
    assert store2['boolscope']['key1'] == 'False'
    assert store2['boolscope']['key2'] == 'True'
    assert store2['scope1']['key1'] == 'scope1.key1'
    assert store2['scope1']['key2'] == 'scope1.key2'
    assert store2['scope2']['key1'] == 'scope2.key1'
    assert store2['scope2']['key2'] == 'scope2.key2'
    assert store2['textlistscope']['key1'] == '["key1.value1", "key1.value2"]'
    assert store2['textlistscope']['key2'] == '["key2.value1", "key2.value2"]'


def test_answerstore_load(answerfile):
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load(answerfile)
    assert 'scope1' in store.keys()
    assert 'scope2' in store.keys()
    assert 'boolscope' in store.keys()
    assert 'key1' in store['scope1'].keys()
    assert 'key1' in store['scope1'].keys()
    assert 'key1' in store['scope2']
    assert 'key2' in store['scope2']
    assert 'key1' in store['boolscope']
    assert 'key2' in store['boolscope']
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['boolscope']['key1'] == 'True'
    assert store['boolscope']['key2'] == 'False'
    assert store['textlistscope']['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    assert store['textlistscope']['key2'] == '["key2.value1", "key2.value2"]'


def test_answerstore_load_and_translate_for_workflow(answerfile):
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load_and_translate_for_workflow(answerfile, MockWorkflow)
    assert store['boolscope']['key1'] is True
    assert store['boolscope']['key2'] is False
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['textlistscope']['key1'] == ["key1.value1", "key1.value2"]
    assert store['textlistscope']['key2'] == ["key2.value1", "key2.value2"]


def test_answerfile_get(monkeypatch, answerfile):
    entries_created = []

    def mocked_create_audit_entry(event, data, message=None):
        entries_created.append((event, data, message))

    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load(answerfile)
    monkeypatch.setattr(leapp.messaging.answerstore, 'create_audit_entry', mocked_create_audit_entry)

    # Testing boolscope
    assert store['boolscope']['key1'] == 'True'
    assert store['boolscope']['key2'] == 'False'
    result = a.get(scope='boolscope', fallback='boolscope')
    assert result != 'boolscope'
    assert result['key1'] == 'True'
    assert result['key2'] == 'False'
    assert entries_created
    assert entries_created[0][1]['scope'] == 'boolscope'
    assert entries_created[0][1]['fallback'] == 'boolscope'
    assert entries_created[0][1]['answer']['key1'] == 'True'
    assert entries_created[0][1]['answer']['key2'] == 'False'
    entries_created.pop()

    # Testing scope1
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    result = a.get(scope='scope1', fallback='scope1')
    assert result
    assert result['key1'] == 'scope1.key1'
    assert result['key2'] == 'scope1.key2'
    assert entries_created
    assert entries_created[0][1]['scope'] == 'scope1'
    assert entries_created[0][1]['fallback'] == 'scope1'
    assert entries_created[0][1]['answer']['key1'] == 'scope1.key1'
    assert entries_created[0][1]['answer']['key2'] == 'scope1.key2'
    entries_created.pop()

    # Testing scope2
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'

    result = a.get(scope='scope2', fallback='scope2')
    assert result
    assert result['key1'] == 'scope2.key1'
    assert result['key2'] == 'scope2.key2'
    assert entries_created
    assert entries_created[0][1]['scope'] == 'scope2'
    assert entries_created[0][1]['fallback'] == 'scope2'
    assert entries_created[0][1]['answer']['key1'] == 'scope2.key1'
    assert entries_created[0][1]['answer']['key2'] == 'scope2.key2'
    entries_created.pop()

    # Testing textlistscope
    assert store['textlistscope']['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    assert store['textlistscope']['key2'] == '["key2.value1", "key2.value2"]'
    result = a.get(scope='textlistscope', fallback='textlistscope')
    assert result
    assert result['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    assert result['key2'] == '["key2.value1", "key2.value2"]'
    assert entries_created
    assert entries_created[0][1]['scope'] == 'textlistscope'
    assert entries_created[0][1]['fallback'] == 'textlistscope'
    assert entries_created[0][1]['answer']['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    assert entries_created[0][1]['answer']['key2'] == '["key2.value1", "key2.value2"]'
    entries_created.pop()


def test_answerfile_translate_for_workflow(answerfile):
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load(answerfile)
    assert store['boolscope']['key1'] == 'True'
    assert store['boolscope']['key2'] == 'False'
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['textlistscope']['key1'] == '[\n"key1.value1",\n"key1.value2"\n]'
    a.translate_for_workflow(MockWorkflow)
    assert store['boolscope']['key1'] is True
    assert store['boolscope']['key2'] is False
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['textlistscope']['key1'] == ["key1.value1", "key1.value2"]
    assert store['textlistscope']['key2'] == ["key2.value1", "key2.value2"]


def test_answerfile_translate(answerfile):
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load(answerfile)
    assert store['boolscope']['key1'] == 'True'
    assert store['boolscope']['key2'] == 'False'
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    a.translate(MockDialogBoolScope)
    a.translate(MockDialogTextListScope)
    assert store['boolscope']['key1'] is True
    assert store['boolscope']['key2'] is False
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['textlistscope']['key1'] == ["key1.value1", "key1.value2"]
    assert store['textlistscope']['key2'] == ["key2.value1", "key2.value2"]


def test_answerfile_generate(tmpdir, answerfile):
    f = tmpdir.join('test_answerfile_generate')
    m = MockManager()
    a = AnswerStore(manager=m)
    store = a._storage
    a.load_and_translate_for_workflow(answerfile, MockWorkflow)
    assert store['scope1']['key1'] == 'scope1.key1'
    assert store['scope1']['key2'] == 'scope1.key2'
    assert store['scope2']['key1'] == 'scope2.key1'
    assert store['scope2']['key2'] == 'scope2.key2'
    assert store['boolscope']['key1'] is True
    assert store['boolscope']['key2'] is False
    assert store['textlistscope']['key1'] == ['key1.value1', 'key1.value2']
    assert store['textlistscope']['key2'] == ['key2.value1', 'key2.value2']
    a.answer('scope1', 'key1', 'generate.scope1.key1')
    a.answer('scope1', 'key2', 'generate.scope1.key2')
    a.answer('scope2', 'key1', 'generate.scope2.key1')
    a.answer('scope2', 'key2', 'generate.scope2.key2')
    a.answer('boolscope', 'key1', False)
    a.answer('boolscope', 'key2', True)
    a.generate(MockWorkflow.dialogs, str(f))
    a = AnswerStore(manager=m)
    store2 = a._storage
    a.load_and_translate_for_workflow(str(f), MockWorkflow)
    assert store2['scope1']['key1'] == 'generate.scope1.key1'
    assert store2['scope1']['key2'] == 'generate.scope1.key2'
    assert store2['scope2']['key1'] == 'generate.scope2.key1'
    assert store2['scope2']['key2'] == 'generate.scope2.key2'
    assert store2['boolscope']['key1'] is False
    assert store2['boolscope']['key2'] is True
    assert store2['textlistscope']['key1'] == ['key1.value1', 'key1.value2']
    assert store2['textlistscope']['key2'] == ['key2.value1', 'key2.value2']


def test__comment_out():
    text = 'A really long line of text.\nYep, with newlines.\n\nCouple of them.'
    expected_text = ('# inikey:             A really long line of text.\n'
                     '#                     Yep, with newlines.\n'
                     '#                     Couple of them.\n')
    key = 'inikey'
    commented_text = _comment_out(key, text)
    assert commented_text == expected_text
    # make sure that text without newlines works as expected
    text = 'A text without newline'
    expected_text = '# inikey:             A text without newline\n'
    assert _comment_out(key, text) == expected_text
