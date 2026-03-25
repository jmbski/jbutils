"""Dict/Class hybrid with dot accessor. Accounts for Lists as well"""

from typing import Any, TypeVar, Iterable

Self = Any
try:
    from typing import Self
except:
    pass

T = TypeVar("T")


class AttrList(list):
    """A list-like object that auto-converts items that are list/dict-like

    to AttrList/AttrDict
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        AttrList.__check_sub__(self)

    @classmethod
    def __check_sub__(cls, items: Any) -> None:
        if issubclass(type(items), list):
            for i, item in enumerate(items):
                items[i] = AttrDict.__check_sub__(item)

    def append(self, obj: Any) -> None:
        return super().append(AttrDict.__check_sub__(obj))

    def extend(self, items: Iterable) -> None:
        AttrList.__check_sub__(items)
        return super().extend(items)


class AttrDict(dict):
    """A dict-like object that also supports attribute-style access.

    Missing keys or attributes return None instead of raising KeyError/AttributeError.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            self[key] = AttrDict.__check_sub__(value)

    @classmethod
    def __check_sub__(cls, value: T) -> T | Self | AttrList:  # type: ignore
        if issubclass(type(value), dict):
            return cls(value)
        if issubclass(type(value), list):
            return AttrList(value)
        return value

    def __getattr__(self, key: str):
        # Called when accessing obj.key
        return self.get(key, None)

    def __setattr__(self, key: str, value: Any):
        # Called when doing obj.key = value

        # self[key] = AttrDict.__check_sub__(value)
        self[key] = value

    def __setitem__(self, key: Any, value: Any) -> None:

        return super().__setitem__(key, AttrDict.__check_sub__(value))

    def __getitem__(self, key: str):
        # Called when doing obj[key]
        return super().get(key, None)

    def __delattr__(self, key: str):
        # Allow del obj.key
        if key in self:
            del self[key]
        else:
            raise AttributeError(f"No such attribute: {key}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"
