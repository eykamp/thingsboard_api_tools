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


from typing import  Optional, Dict, Any
from pydantic import Field

try:
    from .HasAttributes import HasAttributes
    from .TbModel import Id, TbObject
except (ModuleNotFoundError, ImportError):
    from HasAttributes import HasAttributes
    from TbModel import Id, TbObject


class Tenant(TbObject, HasAttributes):
    name: Optional[str] = Field(alias="title")
    tenant_profile_id: Id = Field(alias="tenantProfileId")
    region: Optional[str]
    address: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    additional_info: Optional[Dict[str, Any]] = Field(alias="additionalInfo")


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tenant):       # Probably superfluous -- ids are guids so won't collide
            return False

        return self.id == other.id


    def delete(self) -> bool:
        """
        Deletes the tenant from the server, returns True if tenant was deleted, False if it did not exist
        """
        return self.tbapi.delete(f"/api/tenant/{self.id.id}", f"Error deleting tenant '{self.id.id}'")


    def update(self):
        return self.tbapi.post("/api/tenant", self.model_dump_json(by_alias=True), "Error updating tenant")


    def one_line_address(self) -> str:
        """ Reutrn a 1-line formatted address. """
        return f"{self.address}, {((self.address2 + ', ') if self.address2 else '')} {self.city}, {self.state}"
