"""Model representing the base class for other models"""

from __future__ import annotations

from typing import Any, Self, Optional

from jbutils.types import Predicate


def _update_list_values(
    items: list[Any],
    new_items: list[Any],
    sort: bool = False,
    sort_func: Optional[Predicate[Any]] = None,
    reverse: bool = False,
) -> list[Any]:
    """Add new items to a list and sort it

    Args:
        items (list[Any]): Items to add to
        new_items (list[Any]): Items to add
        sort (Callable[[Any], bool], optional): Custom sort function. Defaults to None.
        reverse (bool, optional): If true, sort order is reversed. Defaults to False.

    Returns:
        list[Any]: The updated list
    """

    for item in new_items:
        if item not in items:
            items.append(item)

    if sort:
        if sort_func:
            items.sort(key=sort_func, reverse=reverse)
        else:
            items.sort(reverse=reverse)

    return items


def _remove_list_values(
    items: list[Any],
    del_items: list[Any],
    sort: bool = False,
    sort_func: Optional[Predicate[Any]] = None,
    reverse: bool = False,
) -> list[Any]:
    """Remove items from a list and sort it

    Args:
        items (list[Any]): Items to remove from
        del_items (list[Any]): Items to remove
        sort (Callable[[Any], bool], optional): Custom sort function. Defaults to None.
        reverse (bool, optional): If true, sort order is reversed. Defaults to False.

    Returns:
        list[Any]: The updated list
    """

    for item in del_items:
        if item in items:
            items.remove(item)
    if sort:
        if sort_func:
            items.sort(key=sort_func, reverse=reverse)
        else:
            items.sort(reverse=reverse)

    return items


class Base:
    """A base class mixin used for extending common features among other classes"""

    def __str__(self) -> str:
        if hasattr(self, "__dataclass_fields__"):
            return super().__str__()

        data = self.to_dict()
        items = []
        for key, value in data.items():
            items.append(f"{key}: {value}")
        return "\n" + "; ".join(items) + "\n"

    def __repr__(self) -> str:
        if hasattr(self, "__dataclass_fields__"):
            return super().__repr__()
        return self.__str__()

    @classmethod
    def from_obj(cls, obj: dict | None | Self) -> Self:
        """Create a new instance of the calling class based on the object

        Args:
            obj (dict | Self): Either a dict object to pass as kwargs to
                the dataclass, or an already instantiated class

        Returns:
            Self: The provided object if it's already converted to the
                class instance, or create a new instance of the class and
                provide the object as kwargs to instantiate it
        """

        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if not hasattr(cls, key) and (
                    not hasattr(cls, "__dataclass_fields__")
                    or key not in getattr(cls, "__dataclass_fields__")
                ):
                    del obj[key]
            return cls(**obj)
        elif obj is None:
            return cls()
        return obj

    def to_dict(self) -> dict:
        """Recursively iterate the class and any child values to return
            a dict version of the entire structure

        Returns:
            dict: A dict representing the class and any children it has
                defined
        """

        def get_value(value: Any) -> Any:
            if isinstance(value, Base):
                return value.to_dict()
            elif isinstance(value, dict):
                return {
                    k: get_value(v)
                    for k, v in value.items()
                    if not k.startswith("_")
                }
            elif isinstance(value, list):
                return [get_value(v) for v in value]
            else:
                return value

        return get_value(vars(self))

    def copy(self) -> Self:
        """Make a new instance of this class with all the same values

        Returns:
            Self: The new copy
        """

        new_instance = self.__class__()
        for key, value in vars(self).items():

            new_value = value
            if hasattr(value, "copy"):
                new_value = value.copy()

            setattr(new_instance, key, new_value)
        return new_instance

    def is_in(self, other: Base) -> bool:
        if other.__class__ != self.__class__:
            return False

        for key, value in vars(self).items():
            if key.startswith("_"):
                continue
            o_value = getattr(other, key)

            if isinstance(value, list) and any(
                item not in o_value for item in value
            ):
                return False
            if isinstance(value, self.__class__):
                if not value.is_in(o_value):
                    return False

        return True

    def update(self, other: Base, remove_included: bool = True) -> None:
        """Update the values of this class from another instance of it

        Args:
            other (Base): Another instance to copy values from
            remove_included (bool, optional): If True, list values from
                other will be removed from the same property in this
                instance. Defaults to True.
        """

        if other.__class__ != self.__class__:
            return

        removing = other.is_in(self) and remove_included

        for key, value in vars(other).items():
            if hasattr(self, key):
                self_value = getattr(self, key)

                if isinstance(value, list):
                    if removing:
                        _remove_list_values(self_value, value)
                    else:
                        _update_list_values(getattr(self, key), value)
                elif isinstance(value, self.__class__):
                    self_value.update(value)
