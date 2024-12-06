from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple


from . import known_labels


@dataclass(frozen=True)
class Label:
    name: str
    value: str


class LabelSet(defaultdict):
    def __init__(self, labels: Iterable[Label]):
        super(LabelSet, self).__init__(list)
        for label in labels:
            self[label.name].append(label.value)

    def covers(self, other: "LabelSet") -> bool:
        """covered means all other must be present in this item's Labels, and all values must match exactly."""
        try:
            for name, value in other.items():
                v = self[name]
                assert v == value
            return True
        except AssertionError as _e:
            print(_e)
            return False
        # return all(self[k] == v for k, v in other.items())

    def __iter__(self) -> Iterator[Label]:
        for k, vs in self.items():
            for v in vs:
                yield Label(name=k, value=v)


@dataclass
class Labeled:
    labels: Iterable[Label] = field(default_factory=list)
    _label_set: LabelSet = field(init=False)

    def __post_init__(self):
        self._label_set = LabelSet(self.labels)

    def covers(self, other: "Labeled"):
        return self._label_set.covers(other._label_set)


@dataclass
class Context:
    ...


Range = Tuple[int, int]


@dataclass
class Excerpt:
    description: str = ""
    # Relative path within the context
    path: str = ""
    # Range within the file [start, end)
    range: Optional[Range] = None
    content: str = ""


@dataclass
class Snippet(Labeled):
    id: str = ""
    context: Optional[Context] = None
    excerpts: List[Excerpt] = field(default_factory=list)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash((self.id))


@dataclass
class Expanded:
    long: str
    short: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Expanded) and self.long == other.long and self.short == other.short

    def __hash__(self):
        return hash((self.long, self.short))


@dataclass
class Sdk(Labeled):
    language: str = ""
    version: str = ""
    name: Optional[Expanded] = None
    guide: str = ""

    def __post_init__(self):
        self.labels = [*self.labels, Label(name=known_labels.SDK, value=f"{self.language}:{self.version}")]
        self._label_set = LabelSet(self.labels)

    def __eq__(self, other):
        return isinstance(other, Sdk) and self.language == other.language and self.version == other.version

    def __hash__(self):
        return hash((self.language, self.version))


@dataclass
class Service(Labeled):
    id: str = ""
    name: Optional[Expanded] = None
    expanded: Optional[Expanded] = None
    sort: str = ""
    version: str = ""
    api_ref: Optional[str] = None
    # guide: Optional[ServiceGuide] = None

    def __post_init__(self):
        self.labels = [*self.labels, Label(name=known_labels.SERVICE, value=f"{self.id}")]
        self._label_set = LabelSet(self.labels)

    def __eq__(self, other):
        return isinstance(other, Service) and self.name == other.name

    def __hash__(self):
        return hash((self.name))


@dataclass
class Example(Labeled):
    id: str = ""
    title: Optional[str] = ""
    title_abbrev: Optional[str] = ""
    synopsis: Optional[str] = ""
    category: Optional[str] = None
    # guide_topic: Optional[Url] = None
    # doc_filenames: Optional[DocFilenames] = None
    synopsis_list: List[str] = field(default_factory=list)

    def __eq__(self, other):
        return isinstance(other, Example) and self.id == other.id

    def __hash__(self):
        return hash((self.id))


def select(items: Iterable[Labeled], for_labels_in: Labeled):
    return_set = set()
    for item in items:
        if item.covers(for_labels_in):
            return_set.add(item)
    return frozenset(return_set)
    # return frozenset(item for item in items if item.covers(for_labels_in))
