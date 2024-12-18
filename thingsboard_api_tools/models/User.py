# Copyright 2018-2024, Chris Eykamp

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

from typing import Any
from pydantic import Field
from .HasAttributes import HasAttributes
from .TbModel import Id, TbObject


# Intended as a read-only model -- there's no reason to create these
class User(TbObject, HasAttributes):
    name: str | None = None
    tenant_id: Id = Field(alias="tenantId")
    customer_id: Id = Field(alias="customerId")
    authority: str              # Permssions; e.g. "SYS_ADMIN, TENANT_ADMIN or CUSTOMER_USER"
    email: str | None
    first_name: str | None = Field(alias="firstName")
    last_name: str | None = Field(alias="lastName")
    phone: str | None
    additional_info: dict[str, Any] | None = Field(alias="additionalInfo")


    def __str__(self) -> str:
        return "User (" + str(self.name or self.first_name + " " + self.last_name) + ", " + str(self.id.id) + ")"      # type: ignore


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False

        return self.id == other.id
