# Stubs for marathon.models.constraint (Python 3.7)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional
from .base import MarathonObject as MarathonObject

class MarathonConstraint(MarathonObject):
    field = ...  # type: Any
    operator = ...  # type: Any
    value = ...  # type: Any
    def __init__(self, field, operator, value: Optional[Any] = ...) -> None: ...
    def json_repr(self, minimal: bool = ...): ...
    @classmethod
    def from_json(cls, obj): ...
