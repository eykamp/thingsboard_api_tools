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
from datetime import datetime
from typing import  Optional, Dict, List, Any, TYPE_CHECKING
from pydantic import Field       # pip install pydantic
from TbModel import TbModel, Id, TbObject


if TYPE_CHECKING:
    from Device import Device


class CustomerId(TbModel):
    """ This is an Id with couple of extra fields. """
    id: Id = Field(alias="customerId")
    public: bool
    title: str

    def __str__(self) -> str:
        return f"CustomerId ({'PUBLIC' if self.public else self.title + ' ,' + self.id.id})"


    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CustomerId):
            other = other.id

        if not isinstance(other, Id):
            return False

        return self.id == other


class Customer(TbObject):
    id: Id
    title: Optional[str]
    created_time: datetime = Field(alias="createdTime")
    tenant_id: Id = Field(alias="tenantId")
    name: Optional[str]
    address: Optional[str]
    address2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    additional_info: Optional[Dict[str, Any]] = Field(alias="additionalInfo")

    def __str__(self) -> str:
        return "Customer (" + str(self.title) + ", " + str(self.id.id) + ")"


    @property
    def customer_id(self) -> CustomerId:
        obj = {"customerId": self.id, "public": self.is_public(), "title": self.title}
        return CustomerId(**obj)


    def get_devices(self) -> List["Device"]:
        """
        Returns a list of all devices associated with a customer
        """
        cust_id = self.id.id

        all_results = self.tbapi.get_paged(f"/api/customer/{cust_id}/devices", f"Error retrieving devices for customer '{cust_id}'")
        return self.tbapi.tb_objects_from_list(all_results, Device)       # Circular... Device gets defined below, but refers to Customer...


    def delete(self) -> bool:
        """
        Deletes the customer from the server, returns True if customer was deleted, False if it did not exist
        """
        return self.tbapi.delete(f"/api/customer/{self.id.id}", f"Error deleting customer '{self.id.id}'")


    def is_public(self) -> bool:
        if not self.additional_info:
            return False
        # else
        return self.additional_info.get("isPublic", False)


    def update(self, **kwargs: Dict[str, Any]):  # dder: str
        #     name: Optional[str] = None,
        #     address: Optional[str] = None,
        #     address2: Optional[str] = None,
        #     city: Optional[str] = None,
        #     state: Optional[str] = None,
        #     zip: Optional[str] = None,
        #     country: Optional[str] = None,
        #     email: Optional[str] = None,
        #     phone: Optional[str] = None,
        #     additional_info: Optional[Dict[str, Any]] = None
        # ):
        """ Updates an existing customer record. Pass in keywords to change. """
        # if "name" in kwargs:
        #     self.name = kwargs["name"]
        # if "address" in kwargs:
        #     self.address = kwargs["address"]
        # if "address2" in kwargs:
        #     self.address2 = kwargs["address2"]
        # if "city" in kwargs:
        #     self.city = kwargs["city"]
        # if "state" in kwargs:
        #     self.state = kwargs["state"]
        # if "zip" in kwargs:
        #     self.zip = kwargs["zip"]
        # if "country" in kwargs:
        #     self.country = kwargs["country"]
        # if "email" in kwargs:
        #     self.email = kwargs["email"]
        # if "phone" in kwargs:
        #     self.phone = kwargs["phone"]
        # if "additional_info" in kwargs:
        #     self.additional_info = kwargs["additional_info"]

        return self.tbapi.post("/api/customer", self.json(by_alias=True), "Error updating customer")

    # def cc(self):
    #     self.update()
