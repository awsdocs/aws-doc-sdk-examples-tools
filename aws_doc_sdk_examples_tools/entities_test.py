import pytest
from .entities import (
    EntityErrors,
    InvalidItemException,
    expand_all_entities,
    MissingEntityError,
)


def test_entity_errors_append():
    errors = EntityErrors()
    errors.append(MissingEntityError("entity1"))
    assert len(errors._errors) == 1
    assert errors._errors[0].entity == "entity1"

    with pytest.raises(InvalidItemException):
        errors.append("invalid item")


def test_expand_missing_entities():
    entity_map = {
        "&entity1;": "expanded1",
        "&entity2;": "expanded2",
    }

    text = "This is a text with &entity1; and &entity2; and &entity3;"
    expanded_text, errors = expand_all_entities(text, entity_map)

    assert expanded_text == "This is a text with expanded1 and expanded2 and &entity3;"
    assert len(errors._errors) == 1
    assert isinstance(errors._errors[0], MissingEntityError)
    assert errors._errors[0].entity == "&entity3;"

def test_expand_empty_entity():
    entity_map = {
        "&entity1;": "expanded1",
        "&entity2;": "expanded2",
        "&entity3;": ""
    }

    text = "This is a text with &entity1; and &entity2; and &entity3;"
    expanded_text, errors = expand_all_entities(text, entity_map)

    assert expanded_text == "This is a text with expanded1 and expanded2 and "
    assert len(errors._errors) == 0

def test_expand_all_entities_with_no_entities():
    entity_map = {
        "&entity1;": "expanded1",
        "&entity2;": "expanded2",
    }

    text = "This is a text with no entities."
    expanded_text, errors = expand_all_entities(text, entity_map)

    assert expanded_text == "This is a text with no entities."
    assert len(errors._errors) == 0
