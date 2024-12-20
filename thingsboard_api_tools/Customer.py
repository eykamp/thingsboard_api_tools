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

from typing import  Optional, Dict, List, Any, TYPE_CHECKING
from pydantic import Field       # pip install pydantic

try:
    from .HasAttributes import HasAttributes
    from .TbModel import TbModel, Id, TbObject
except (ModuleNotFoundError, ImportError):
    from HasAttributes import HasAttributes
    from TbModel import TbModel, Id, TbObject


if TYPE_CHECKING:
    from Device import Device


class CustomerId(TbModel):
    """ This is an Id with couple of extra fields. """

    # from TbModel import TbModel, Id, TbObject

    id: Id = Field(alias="customerId")
    public: bool
    name: str = Field(alias="title")


    def __str__(self) -> str:
        return f"CustomerId ({'PUBLIC' if self.public else self.name})"


    def __eq__(self, other: Any) -> bool:
        return self.id == other     # We'll put all the weird cases in Id's __eq__ and redirect ourselves there


class Customer(TbObject, HasAttributes):
    name: str = Field(alias="title")      # "title" is the oficial TB name field; "name" is read-only, maps to this
    tenant_id: Id = Field(alias="tenantId")
    address: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    additional_info: Optional[Dict[str, Any]] = Field(default={}, alias="additionalInfo")


    def update(self):
        return self.tbapi.post("/api/customer", self.model_dump_json(by_alias=True), "Error updating customer")


    def is_public(self) -> bool:
        if not self.additional_info:
            return False
        # else
        return self.additional_info.get("isPublic", False)


    def one_line_address(self) -> str:
        """ Reutrn a 1-line formatted address. """
        return f"{self.address}, {((self.address2 + ', ') if self.address2 else '')} {self.city}, {self.state}"


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return False

        return self.id == other.id


    @property
    def customer_id(self) -> CustomerId:
        return CustomerId(customerId=self.id, public=self.is_public(), title=self.name if self.name else "")


    def get_devices(self) -> List["Device"]:
        """
        Returns a list of all devices associated with a customer; will not include public devices!
        """
        try:
            from .Device import Device
        except ModuleNotFoundError:
            from Device import Device

        cust_id = self.id.id

        all_results = self.tbapi.get_paged(f"/api/customer/{cust_id}/devices", f"Error retrieving devices for customer '{cust_id}'")
        return self.tbapi.tb_objects_from_list(all_results, Device)       # Circular... Device gets defined below, but refers to Customer...


    def delete(self) -> bool:
        """
        Deletes the customer from the server, returns True if customer was deleted, False if it did not exist
        """
        return self.tbapi.delete(f"/api/customer/{self.id.id}", f"Error deleting customer '{self.id.id}'")
