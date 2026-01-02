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

from typing import  Optional, Dict, List, Any, Union, Iterable, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from pydantic import Field

from .TbModel import TbObject, Id
from .HasAttributes import HasAttributes
from .DeviceProfile import DeviceProfile, DeviceProfileInfo


if TYPE_CHECKING:
    from .TbModel import TbApi
    from .Customer import Customer


Timestamp = Union[datetime, float]


class AggregationType(Enum):
    MIN = "MIN"
    MAX = "MAX"
    AVG = "AVG"
    SUM = "SUM"
    COUNT = "COUNT"
    NONE = "NONE"


class Device(TbObject, HasAttributes):
    additional_info: Optional[Dict[str, Any]] = Field(default={}, alias="additionalInfo")
    tenant_id: Id = Field(alias="tenantId")
    customer_id: Id = Field(alias="customerId")
    name: Optional[str]
    type: Optional[str]
    label: Optional[str]
    device_profile_id: Id = Field(alias="deviceProfileId")
    software_id: Optional[str] = Field(alias="softwareId")
    firmware_id: Optional[str] = Field(alias="firmwareId")

    _device_token: Optional[str] = None

    def __type_hints__(self, device_token: str):
        """ Dummy method to annotate the instance attribute types """
        self._device_token = device_token


    def __init__(self, tbapi: "TbApi", *args: List[Any], **kwargs: Dict[str, Any]):
        """ Create an initializer to handle our slot fields; other fields handled automatically by Pydantic. """
        super().__init__(tbapi=tbapi, *args, **kwargs)
        object.__setattr__(self, "device_token", None)  # type: str
        pass


    def delete(self) -> bool:
        """ Returns True if device was deleted, False if it did not exist """
        return self.tbapi.delete(f"/api/device/{self.id.id}", f"Error deleting device '{self.id.id}'")


    def assign_to(self, customer: "Customer") -> None:
        if self.customer_id != customer.id:
            obj = self.tbapi.post(f"/api/customer/{customer.id.id}/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to customer {customer}")
            self.customer_id = Id.model_validate(obj["customerId"])


    def get_customer(self) -> Optional["Customer"]:
        """ Returns the customer assigned to the device, or None if the device is unassigned. """
        return self.tbapi.get_customer_by_id(self.customer_id)


    def make_public(self) -> None:
        """ Assigns device to the public customer, which is how TB makes devices public. """
        if not self.is_public():
            obj = self.tbapi.post(f"/api/customer/public/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to public customer")
            self.customer_id = Id.model_validate(obj["customerId"])


    def is_public(self) -> bool:
        """ Return True if device is owned by the public user, False otherwise """
        public_id = self.tbapi.get_public_user_id()
        if not public_id:
            return False

        return public_id == self.customer_id


    def get_profile(self) -> DeviceProfile:
        return self.tbapi.get_device_profile_by_id(self.device_profile_id)


    def get_profile_info(self) -> DeviceProfileInfo:
        return self.tbapi.get_device_profile_info_by_id(self.device_profile_id)


    def get_telemetry(
        self,
        keys: Union[str, Iterable[str]],
        start_ts: Optional[Timestamp] = None,
        end_ts: Optional[Timestamp] = None,
        interval: Optional[int] = None,
        limit: int = 100,               # Just to keep things sane
        agg: AggregationType = AggregationType.NONE,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        keys: Pass a single key or a list of keys
        Note: Returns a sane amount of data by default, in same shape as get_latest_telemetry()
        """
        if isinstance(keys, str):
            keys = keys
        else:
            keys = ",".join(keys)

        # Don't include these in the signature because datetime.now() gets evaluated once when function is first called, then reused after that.
        # It's lame, but it's the way default values are managed in Python.  Blame Guido.
        # Same principle as this: https://web.archive.org/web/20201002220217/http://effbot.org/zone/default-values.htm
        if start_ts is None:
            start_ts = 0
        if end_ts is None:
            end_ts = datetime.now()


        start_ts = prepare_ts(start_ts)
        end_ts = prepare_ts(end_ts)

        # These are all optional parameters, strictly speaking
        interval_clause = f"&interval={interval}" if interval else ""
        limit_caluse = f"&limit={limit}" if limit else ""
        agg_clause = f"&agg={agg.value}"
        use_strict_datatypes_clause = "&useStrictDataTypes=true"       # Fixes bug of getting back strings as numbers

        clauses = interval_clause + limit_caluse + agg_clause + use_strict_datatypes_clause
        params = f"/api/plugins/telemetry/DEVICE/{self.id.id}/values/timeseries?keys={keys}&startTs={start_ts}&endTs={end_ts}{clauses}"

        error_message = f"Error retrieving telemetry for device '{self}' with date range '{start_ts}-{end_ts}' and keys '{keys}'"

        return self.tbapi.get(params, error_message)
        # https://demo.thingsboard.io/swagger-ui.html#/telemetry-controller/getTimeseriesUsingGET


    def send_telemetry(self, data: Dict[str, Any], ts: Optional[Timestamp | int] = None):
        if not data:
            return

        if ts is not None:
            data = {"ts": prepare_ts(ts), "values": data}

        return self.tbapi.post(f"/api/v1/{self.token}/telemetry", data, f"Error sending telemetry for device '{self.name}'")
        # scope = "LATEST_TELEMETRY"
        # return self.tbapi.post(f"/api/plugins/telemetry/DEVICE/{self.token}/timeseries/{scope}", data, f"Error sending telemetry for device '{self.name}'")

        # /api/plugins/telemetry/{entityType}/{entityId}/timeseries/{scope}
    # https://demo.thingsboard.io/swagger-ui.html#/telemetry-controller/saveEntityAttributesV1UsingPOST


    def get_telemetry_keys(self) -> List[str]:
        return self.tbapi.get(f"/api/plugins/telemetry/DEVICE/{self.id.id}/keys/timeseries", f"Error retrieving telemetry keys for device '{self.id.id}'")


    def get_latest_telemetry(self, keys: str | Iterable[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Pass a single key, a stringified comma-separate list, a list object, or a tuple
        get_latest_telemetry(['datum_1', 'datum_2']) ==>
            {'datum_1': [{'ts': 1595897301000, 'value': '555'}], 'datum_2': [{'ts': 1595897301000, 'value': '666'}]}

        """
        if not isinstance(keys, str):
            keys = ",".join(keys)

        use_strict_datatypes_clause = "&useStrictDataTypes=true"        # Fixes bug of getting back strings as numbers
        url = f"/api/plugins/telemetry/DEVICE/{self.id.id}/values/timeseries?keys={keys}{use_strict_datatypes_clause}"

        return self.tbapi.get(url, f"Error retrieving latest telemetry for device '{self.id.id}' with keys '{keys}'")


    def delete_all_telemetry(self, keys: Union[str, List[str]]):
        """ Danger, Will Robinson!  Deletes all device data for the specified key(s).  """
        if isinstance(keys, str):
            keys = [keys]

        params = f"keys={','.join(keys)}&deleteAllDataForKeys=True"

        return self.tbapi.delete(f"/api/plugins/telemetry/DEVICE/{self.id.id}/timeseries/delete?{params}", f"Error deleting telemetry for device '{self.id.id}' with params '{params}'")
        # https://demo.thingsboard.io/swagger-ui.html#/telemetry-controller/deleteEntityTimeseriesUsingDELETE


    def delete_telemetry(
        self,
        keys: Union[str, List[str]],
        start_ts: Timestamp,
        end_ts: Timestamp,
        rewrite_latest_if_deleted: bool = False,
    ) -> bool:
        """
        Delete specified telemetry between start_ts and end_ts.
        rewrite_latest_if_deleted: True if the server should update ts_kv_latest; False if the server should obliterate ts_kv_latest
            by writing a record with current timestamp and a value of None.
        Returns True if request succeeded, whether or not telemetry was actually deleted, False if there was a problem.
        """
        if isinstance(keys, str):
            keys = [keys]

        start_ts = prepare_ts(start_ts)
        end_ts = prepare_ts(end_ts)

        params = f"keys={','.join(keys)}&startTs={start_ts}&endTs={end_ts}&rewriteLatestIfDeleted={rewrite_latest_if_deleted}&deleteAllDataForKeys=False"

        return self.tbapi.delete(f"/api/plugins/telemetry/DEVICE/{self.id.id}/timeseries/delete?{params}", f"Error deleting telemetry for device '{self.id.id}' with params '{params}'")
        # https://demo.thingsboard.io/swagger-ui.html#/telemetry-controller/deleteEntityTimeseriesUsingDELETE


    @property
    def token(self) -> str:
        """ Returns the device's secret token from the server and caches it for reuse. """
        if self._device_token is None:
            obj = self.tbapi.get(f"/api/device/{self.id.id}/credentials", f"Error retreiving device_key for device '{self}'")
            self._device_token = obj["credentialsId"]

        if self._device_token is None:
            raise Exception(f"Could not find token for device '{self}'")

        return self._device_token


    def update(self):
        """
        Writes object back to the database.  Use this if you want to save any modified properties.
        """
        return self.tbapi.post("/api/device", self.model_dump_json(by_alias=True), f"Error updating '{self.id.id}'")
        # https://demo.thingsboard.io/swagger-ui.html#/device-controller/saveDeviceUsingPOST


def prepare_ts(ts: Timestamp) -> int:
    if isinstance(ts, datetime):
        ts = ts.timestamp() * 1000

    return int(ts)
