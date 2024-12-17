# Copyright 2018-2019, Chris Eykamp

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import  Dict, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import pytz
from ..TbApi import TbApi

TIMEZONE = pytz.timezone("US/Pacific")


class TbModel(BaseModel):
    """
    Class from which all TbApi classes are descended.  BaseModel is a pydantic class that handles
    most of our dirty work such as encoding, decoding, and validating json streams.
    """
    class Config:
        arbitrary_types_allowed=True        # TODO: Can we get rid of this somehow?
        # json_encoders: Dict[Any, Callable[[Any], Any]] = {      # TODO: json_encoders is deprecated
        #     datetime: lambda v: int(v.timestamp() * 1000),     # TB expresses datetimes as epochs in milliseonds
        # }

    def __repr__(self) -> str:
        return self.__str__()


class Id(TbModel):
    """ Basic ID class. """
    id: str
    # entity_type: str = Field(default_factory=self.xxx, alias="entityType")
    entity_type: str = Field(alias="entityType")


    def __eq__(self, other: Any) -> bool:
        from .Customer import CustomerId

        if isinstance(other, CustomerId):
            return self.id == other.id.id

        if isinstance(other, str):
            return self.id == other

        if isinstance(other, Id):
            return self.id == other.id

        # Not sure what we were passed... but it's probably not an id
        return False


    def __str__(self) -> str:
        return f"Id ({self.entity_type}, {self.id})"


class TbObject(TbModel):
    id: Id
    created_time: datetime | None = Field(default=None, alias="createdTime", exclude=True)       # Read-only attribute

    tbapi: TbApi = Field(exclude=True)


    def __str__(self) -> str:
        name = ""
        if hasattr(self, "name"):
            name = self.name   # type: ignore

        return f"{self.__class__.__name__} ({name + ', ' if name else ''}id={self.id.id})"


class Attribute(BaseModel):
    key: str
    value: Any
    last_updated: datetime = Field(alias="lastUpdateTs")


class Attributes(Dict[str, Attribute]):
    """
    A type of dict specialized for holding Thingsboard attribute data.
    Generally, users won't create these themselves, but will get them from methods
    that return them.
    """

    class Scope(Enum):
        SERVER = "SERVER_SCOPE"
        SHARED = "SHARED_SCOPE"
        CLIENT = "CLIENT_SCOPE"


    """ Represents a set of attributes about an object. """
    def __init__(self, attribute_data: List[Dict[str, Any]], scope: Scope):
        super().__init__()

        for data in attribute_data:
            self[data["key"]] = Attribute(**data)

        self.scope = scope


    def as_dict(self) -> dict[str, Any]:
        """ Collapse Attributes into a simple key/value dictionary. """
        attr_dict: dict[str, Any] = {}

        for attribute in self.values():
            attr_dict[attribute.key] = attribute.value
        return attr_dict
