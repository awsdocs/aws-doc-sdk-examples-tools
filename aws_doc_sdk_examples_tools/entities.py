from typing import List, Optional, TypeVar, Dict, Set, Union, Tuple, Iterator, Iterable
from dataclasses import dataclass
import re

K = TypeVar("K")


class InvalidItemException(Exception):
    def __init__(self, item: K):
        super().__init__(self, f"Cannot append {item!r} to EntityErrors")


@dataclass
class EntityError:
    """
    Base error. Do not use directly.
    """

    entity: Optional[str]

    def message(self) -> str:
        return ""


@dataclass
class MissingEntityError(EntityError):
    def message(self):
        return f"{self.entity} not found."


class EntityErrors:
    def __init__(self):
        self._errors: List[EntityError] = []

    def append(self, maybe_error: Union[K, EntityError]):
        if not isinstance(maybe_error, EntityError):
            raise InvalidItemException(maybe_error)
        self._errors.append(maybe_error)

    def extend(self, errors: Iterable[EntityError]):
        self._errors.extend(errors)

    def __getitem__(self, key: int) -> EntityError:
        return self._errors[key]

    def __setitem__(self, key: int, value: EntityError):
        self._errors[key] = value

    def __len__(self) -> int:
        return len(self._errors)

    def __iter__(self) -> Iterator[EntityError]:
        return self._errors.__iter__()

    def __repr__(self) -> str:
        return repr(self._errors)

    def __str__(self) -> str:
        errs = "\n".join([f"\t{err}" for err in self._errors])
        return f"EntityErrors with {len(self)} errors:\n{errs}"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, EntityErrors) and self._errors == __value._errors


def expand_all_entities(
    text: str, entity_map: Dict[str, str]
) -> Tuple[str, EntityErrors]:
    errors = EntityErrors()
    entities = find_all_entities(text)

    for entity in entities:
        expanded, error = expand_entity(entity, entity_map)
        if error:
            errors.append(error)
        else:
            text = text.replace(entity, expanded)

    return text, errors


def find_all_entities(text: str) -> Set[str]:
    return set(re.findall(r"&[\dA-Za-z-_]+;", text))


def expand_entity(
    entity: str, entity_map: Dict[str, str]
) -> Tuple[str, Optional[EntityError]]:
    expanded = entity_map.get(entity)
    if expanded is not None:
        return entity.replace(entity, expanded), None
    else:
        return entity, MissingEntityError(entity)
