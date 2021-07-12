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
import time
from typing import  Optional, Dict, List, Any, Union, Iterable, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from pydantic import Field
from TbModel import TbObject, Id

if TYPE_CHECKING:
    from TbApi import TbApi
    from Customer import Customer


class AttributeScope(Enum):
    SERVER = "SERVER_SCOPE"
    SHARED = "SHARED_SCOPE"
    CLIENT = "CLIENT_SCOPE"


class AggregationType(Enum):
    MIN = "MIN"
    MAX = "MAX"
    AVG = "AVG"
    SUM = "SUM"
    COUNT = "COUNT"
    NONE = "NONE"


class Device(TbObject):
    id: Id
    additional_info: Optional[Dict[str, Any]] = Field(alias="additionalInfo")
    tenant_id: Id = Field(alias="tenantId")
    customer_id: Id = Field(alias="customerId")
    name: Optional[str]
    type: Optional[str]
    label: Optional[str]
    created_time: datetime = Field(alias="createdTime")

    __slots__ = ["device_token"]

    def __type_hints__(self, device_token: str):
        """ Dummy method to annotate the instance attribute types """
        self.device_token = device_token


    def __init__(self, tbapi: "TbApi", *args: List[Any], **kwargs: Dict[str, Any]):
        """ Create an initializer to handle our slot fields; other fields handled automatically by Pydantic. """
        super().__init__(tbapi, *args, **kwargs)
        object.__setattr__(self, "device_token", None)  # type: str
        pass


    def __str__(self):
        return f"{self.id}/{self.name}"


    def delete(self) -> bool:
        """ Returns True if device was deleted, False if it did not exist """
        return self.tbapi.delete(f"/api/device/{self.id.id}", f"Error deleting device '{self.id.id}'")


    def assign_to(self, customer: "Customer") -> None:
        if self.customer_id != customer.id:
            obj = self.tbapi.post(f"/api/customer/{customer.id.id}/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to customer {customer}")
            self.customer_id = Id(**obj["customerId"])


    def get_customer(self) -> "Customer":
        """ Returns the customer assigned to the device """
        return self.tbapi.get_customer_by_id(self.customer_id)


    def make_public(self) -> None:
        """ Assigns device to the public customer, which is how TB makes devices public. """
        if not self.is_public():
            obj = self.tbapi.post(f"/api/customer/public/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to public customer")
            self.customer_id = Id(**obj["customerId"])


    def is_public(self) -> bool:
        """ Return True if device is owned by the public user, False otherwise """
        return self.tbapi.get_public_user_id() == self.customer_id


    # TODO: Fix
    # def delete_telemetry(self, key, timestamp):
    #     return self.tbapi.delete(f"/api/plugins/telemetry/DEVICE/{self.id.id}/timeseries/values?key={key}&ts={str(int(timestamp))}", f"Error deleting telemetry for device '{self.id.id}'")
    # From swagger: /api/plugins/telemetry/{entityType}/{entityId}/timeseries/delete{?keys,deleteAllDataForKeys,startTs,endTs,rewriteLatestIfDeleted}
    # http://www.sensorbot.org:8080/swagger-ui.html#!/telemetry-controller/deleteEntityTimeseriesUsingDELETE


    def get_telemetry(
        self,
        telemetry_keys: Union[str, Iterable[str]],
        startTime: int = 0,
        endTime: int = int(time.time() * 1000),     # Unix timestamp, now, convert to milliseconds
        interval: int = 60 * 1000,                  # 1 minute
        limit: int = 100,
        agg: AggregationType = AggregationType.NONE
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pass a single key, a stringified comma-separate list, a list object, or a tuple
        Note: Returns a sane amount of data by default, in same shape as get_latest_telemetry()
        """
        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ",".join(telemetry_keys)

        params = f"/api/plugins/telemetry/DEVICE/{self.id.id}/values/timeseries?keys={keys}&startTs=" + \
                 f"{int(startTime)}&endTs={int(endTime)}&interval={interval}&limit={limit}&agg={agg.value}"

        error_message = f"Error retrieving telemetry for device '{self}' with date range '{startTime}-{endTime}' and keys '{keys}'"

        return self.tbapi.get(params, error_message)


    def send_telemetry(self, data: Dict[str, Any], timestamp: int = 0):
        if not data:
            return

        if timestamp:
            data = {"ts": timestamp, "values": data}

        return self.tbapi.post(f"/api/v1/{self.token}/telemetry", data, f"Error sending telemetry for device '{self.name}'")


    def get_telemetry_keys(self) -> List[str]:
        return self.tbapi.get(f"/api/plugins/telemetry/DEVICE/{self.id.id}/keys/timeseries", f"Error retrieving telemetry keys for device '{self.id.id}'")


    def get_latest_telemetry(self, telemetry_keys: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pass a single key, a stringified comma-separate list, a list object, or a tuple
        get_latest_telemetry(['datum_1', 'datum_2']) ==>
            {'datum_1': [{'ts': 1595897301000, 'value': '555'}], 'datum_2': [{'ts': 1595897301000, 'value': '666'}]}

        """
        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ",".join(telemetry_keys)

        return self.tbapi.get(f"/api/plugins/telemetry/DEVICE/{self.id.id}/values/timeseries?keys={keys}", f"Error retrieving latest telemetry for device '{self.id.id}' with keys '{keys}'")


    @property
    def token(self) -> str:
        """ Returns the device's secret token from the server and caches it for reuse. """
        if self.device_token is None:
            obj = self.tbapi.get(f"/api/device/{self.id.id}/credentials", f"Error retreiving device_key for device '{self}'")
            object.__setattr__(self, "device_token", obj["credentialsId"])     # self.device_token = ... won't work with __slot__ attribute
        return self.device_token


    # getting attributes from the server
    def get_server_attributes(self) -> List[Dict[str, Any]]:
        """ Returns a list of the device's attributes in a the Server scope. """
        return self.get_attributes(AttributeScope.SERVER)


    def get_shared_attributes(self) -> List[Dict[str, Any]]:
        """ Returns a list of the device's attributes in a the Shared scope. """
        return self.get_attributes(AttributeScope.SHARED)


    def get_client_attributes(self) -> List[Dict[str, Any]]:
        """ Returns a list of the device's attributes in a the Client scope. """
        return self.get_attributes(AttributeScope.CLIENT)


    def get_attributes(self, scope: AttributeScope) -> List[Dict[str, Any]]:
        """
        Returns a list of the device's attributes in the specified scope.
        Looks like [{'key': 'active', 'lastUpdateTs': 1595969455329, 'value': False}, ...]
        """
        return self.tbapi.get(f"/api/plugins/telemetry/DEVICE/{self.id.id}/values/attributes/{scope.value}", f"Error retrieving {scope.value} attributes for '{self.id.id}'")


    # setting attributes to the server
    def set_server_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Posts the attributes provided (use dict format) to the server in the Server scope
        """
        return self.set_attributes(attributes, AttributeScope.SERVER)


    def set_shared_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Posts the attributes provided (use dict format) to the server in the Shared scope
        """
        return self.set_attributes(attributes, AttributeScope.SHARED)


    def set_client_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Posts the attributes provided (use dict format) to the server in the Client scope
        """
        return self.set_attributes(attributes, AttributeScope.CLIENT)


    def set_attributes(self, attributes: Dict[str, Any], scope: AttributeScope) -> Dict[str, Any]:  # Always seems to be empty {}
        """ Posts the attributes provided (use dict format) to the server at a specified scope """
        return self.tbapi.post(f"/api/plugins/telemetry/DEVICE/{self.id.id}/{scope.value}", attributes, f"Error setting {scope.value} attributes for device '{self.id.id}'")


    # def set_attributes_old(self, device, attributes, scope):
    #     device_id = self.get_id(device)
    #     return self.post(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}", attributes, f"Error setting {scope} attributes for device '{device}'")


    # deleting attributes from the server
    def delete_server_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.SERVER)


    def delete_shared_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.SHARED)


    def delete_client_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.CLIENT)


    def delete_attributes(self, attributes: Union[str, Iterable[str]], scope: AttributeScope) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        if not isinstance(attributes, str):
            attributes = ",".join(attributes)

        return self.tbapi.delete(f"/api/plugins/telemetry/DEVICE/{self.id.id}/{scope.value}?keys={attributes}", f"Error deleting {scope.value} attributes for device '{self.id.id}'")
