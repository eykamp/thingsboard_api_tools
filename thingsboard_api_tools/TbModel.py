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

# Update with: pip install git+git://github.com/eykamp/thingsboard_api_tools.git --upgrade

# pyright: strict
from typing import  Optional, Dict, List, Any, Callable, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field       # pip install pydantic

if TYPE_CHECKING:
    from TbApi import TbApi


class TbModel(BaseModel):
    """ Class from which all TbApi classes are descended.  BaseModel is a pydantic class that handles most of our dirty work. """
    class Config:
        json_encoders: Dict[Any, Callable[[Any], Any]] = {
            datetime: lambda v: int(v.timestamp() * 1000),     # TB expresses datetimes as epochs in milliseonds
        }

    def __repr__(self) -> str:
        return self.__str__()


class Id(TbModel):
    """ Basic ID class. """
    id: str
    entity_type: Optional[str] = Field(alias="entityType")


    def __str__(self) -> str:
        return f"Id ({self.entity_type}, {self.id})"


class TbObject(TbModel):
    __slots__ = ["tbapi"]   # Use __slots__ to hide field from pydantic; but they still need to have their types declared.
                            # See https://stackoverflow.com/questions/52553143/slots-type-annotations-for-python-pycharm

    def __init__(self, tbapi: "TbApi", *args: List[Any], **kwargs: Dict[str, Any]):
        # type: (TbApi, Any, Any) -> None
        super().__init__(*args, **kwargs)       # value is not a valid dict (type=type_error.dict)

        object.__setattr__(self, "tbapi", tbapi)


    def __type_hints__(self, tbapi: "TbApi"):
        """
        Dummy method to annotate the instance attribute types.  That is, tbapi is defined in a __slot__, and as of this writing, there is no
        good way to document its type.  This method exists only to inject the concept that self.tbapi is of type TbApi that would otherwise
        not be expressible.  The code here will never get run.
        """
        self.tbapi = tbapi
