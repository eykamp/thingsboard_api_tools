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

import json
import requests
import time
from http import HTTPStatus
from typing import  Optional, Dict, List, Any, Union, Type, Iterable, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AttributeScope(Enum):
    SERVER = "SERVER_SCOPE"
    SHARED = "SHARED_SCOPE"
    CLIENT = "CLIENT_SCOPE"


class EntityType(Enum):
    CUSTOMER = "CUSTOMER"
    DASHBOARD = "DASHBOARD"
    DEVICE = "DEVICE"


class Aggregation(Enum):
    MIN = "MIN"
    MAX = "MAX"
    AVG = "AVG"
    SUM = "SUM"
    COUNT = "COUNT"
    NONE = "NONE"


class TbModel(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp() * 1000),  # TB expresses datetimes as epochs in milliseonds
        }

    def __repr__(self) -> str:
        return self.__str__()


class TbObject(TbModel):
    __slots__ = ["tbapi"]   # Use __slots__ to hide field from pydantic

    def __init__(self, tbapi: "TbApi", *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "tbapi", tbapi)


class Id(TbModel):
    id: str
    entity_type: Optional[str] = Field(alias="entityType")

    def __str__(self) -> str:
        return f"Id ({self.entity_type}, {self.id})"


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
    additional_info: Optional[Dict] = Field(alias="additionalInfo")

    def __str__(self) -> str:
        return "Customer (" + str(self.title) + ", " + str(self.id.id) + ")"

    def get_devices(self):
        """
        Returns a list of all devices associated with a customer
        """
        cust_id = self.id.id

        return self.tbapi.get(f"/api/customer/{cust_id}/devices?limit=99999", f"Error retrieving devices for customer '{cust_id}'")["data"]

    def delete(self):
        """
        Deletes the customer from the server
        """
        return self.tbapi.delete(f"/api/customer/{self.id.id}", f"Error deleting customer '{self.id.id}'")


    def is_public(self) -> bool:
        if not self.additional_info:
            return False
        # else
        return self.additional_info.get("isPublic", False)


    def update(self, **kwargs):  # dder: str
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


class CustomerId(TbModel):
    customer_id: Id = Field(alias="customerId")
    public: bool
    title: str

    def __str__(self) -> str:
        return f"CustomerId ({self.title}, {self.customer_id.id})"


class Device(TbObject):
    id: Id
    additional_info: Optional[dict] = Field(alias="additionalInfo")
    tenant_id: Id = Field(alias="tenantId")
    customer_id: Id = Field(alias="customerId")
    name: Optional[str]
    type: Optional[str]
    label: Optional[str]
    created_time: datetime = Field(alias="createdTime")

    __slots__ = ["device_token"]
    # device_token: str # = None     # call self.get_token() to retrieve and cache the device token from the server

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "device_token", None)
        pass


    def delete(self):
        """ Returns True if device was deleted, False if it did not exist """
        return self.tbapi.delete(f"/api/device/{self.id.id}", f"Error deleting device '{self.id.id}'")


    def assign_to(self, customer: Customer) -> None:
        if device.customer_id != customer.id:
            obj = self.tbapi.post(f"/api/customer/{customer.id.id}/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to customer {customer}")
            self.customer_id = Id(**obj["customerId"])


    def get_customer(self) -> Customer:
        """ Returns the customer assigned to the device """
        return self.tbapi.get_customer_by_id(self.customer_id)


    def make_public(self) -> None:
        """ Assigns device to the public customer, which is how TB makes devices public. """

        if not self.is_public():
            obj = self.tbapi.post(f"/api/customer/public/device/{self.id.id}", None, f"Error assigning device '{self.id.id}' to public customer")
            self.customer_id = Id(**obj["customerId"])


    def is_public(self) -> bool:
        """ Return True if device is owned by the public user, False otherwise """
        pub_id = self.tbapi.get_public_user_id()
        return self.customer_id.id == pub_id


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
        agg: Aggregation = Aggregation.NONE
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
        """ Note that this requires the device's secret token as the first argument """
        if not data:
            return

        device_token = self.get_token()

        if timestamp:
            data = {"ts": timestamp, "values": data}

        return self.tbapi.post(f"/api/v1/{device_token}/telemetry", str(data), f"Error sending telemetry for device with token '{device_token}'")


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


    def get_token(self) -> str:
        """ Returns the device's secret token from the server and caches it """
        if self.device_token is None:
            obj = self.tbapi.get(f"/api/device/{self.id.id}/credentials", f"Error retreiving device_key for device '{self.id.id}'")
            object.__setattr__(self, "device_token", obj["credentialsId"])
            # self.device_token = obj["credentialsId"]
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
    def set_server_attributes(self, attributes: Dict[str, Any]):
        """
        Posts the attributes provided (use dict format) to the server in the Server scope
        """
        return self.set_attributes(attributes, AttributeScope.SERVER)


    def set_shared_attributes(self, attributes: Dict[str, Any]):
        """
        Posts the attributes provided (use dict format) to the server in the Shared scope
        """
        return self.set_attributes(attributes, AttributeScope.SHARED)


    def set_client_attributes(self, attributes: Dict[str, Any]):
        """
        Posts the attributes provided (use dict format) to the server in the Client scope
        """
        return self.set_attributes(attributes, AttributeScope.CLIENT)


    def set_attributes(self, attributes: Dict[str, Any], scope: AttributeScope):
        """ Posts the attributes provided (use dict format) to the server at a specified scope """
        return self.tbapi.post(f"/api/plugins/telemetry/DEVICE/{self.id.id}/{scope.value}", attributes, f"Error setting {scope.value} attributes for device '{self.id.id}'")


    # def set_attributes_old(self, device, attributes, scope):
    #     device_id = self.get_id(device)
    #     return self.post(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}", attributes, f"Error setting {scope} attributes for device '{device}'")


    # deleting attributes from the server
    def delete_server_attributes(self, attributes: Dict[str, Any]):
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.SERVER)


    def delete_shared_attributes(self, attributes: Dict[str, Any]):
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.SHARED)


    def delete_client_attributes(self, attributes: Union[str, Iterable[str]]):
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        return self.delete_attributes(attributes, AttributeScope.CLIENT)


    def delete_attributes(self, attributes: Union[str, Iterable[str]], scope: AttributeScope):
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        if isinstance(attributes, Iterable) and not isinstance(attributes, str):
            attributes = ",".join(attributes)

        return self.tbapi.delete(f"/api/plugins/telemetry/DEVICE/{self.id.id}/{scope.value}?keys={attributes}", f"Error deleting {scope.value} attributes for device '{self.id.id}'")



T = TypeVar("T", Customer, Device)


def _exact_match(name: str, object_list: List[T]) -> Optional[T]:
    matches = []
    for obj in object_list:
        if obj.name == name:
            matches.append(obj)

    if not matches:
        return None

    # Check that all matches are equivalent
    for obj in matches:
        if obj != matches[0]:
            raise Exception(f"multiple matches were found for name {name}")

    return matches[0]



class Widget(TbModel):
    id: Union[Id, str]      # in a DashboardDef, widgets have GUIDs for ids; other times they have full-on Id objects
    is_system_type: bool = Field(alias="isSystemType")
    bundle_alias: str = Field(alias="bundleAlias")
    type_alias: str = Field(alias="typeAlias")
    type: str
    title: str
    size_x: int = Field(alias="sizeX")
    size_y: int = Field(alias="sizeY")
    config: dict
    # index: str

    def __str__(self) -> str:
        return f"Widget ({self.title}, {self.type}, {self.index})"


class SubWidget(TbModel):      # used within States <- Layouts <- Main <- Widgets
    size_x: int = Field(alias="sizeX")
    size_y: int = Field(alias="sizeY")
    mobile_height: Optional[int] = Field(alias="mobileHeight")
    row: int
    col: int
    # index: str

    def __str__(self) -> str:
        return f"SubWidget ({self.index})"


class GridSetting(TbModel):        # used within States <- Layouts <- Main <- GridSetting
    background_color: str = Field(alias="backgroundColor")  # "#3e4b6b",
    color: str  # "rgba(1, 1, 1, 0.87)",
    columns: int
    margins: list  # [10, 10],
    background_size_mode: str = Field(alias="backgroundSizeMode")  # "100%",
    auto_fill_height: bool = Field(alias="autoFillHeight")
    mobile_auto_fill_height: bool = Field(alias="mobileAutoFillHeight")
    mobile_row_height: int = Field(alias="mobileRowHeight")

    def __str__(self) -> str:
        return f"GridSetting"


class Layout(TbModel):      # used within States <- Layouts <- Main <- Widgets
    widgets: Dict[str, SubWidget]
    grid_settings: GridSetting = Field(alias="gridSettings")
    # index: str          # new name of the layout

    def __str__(self) -> str:
        return f"Layout ({len(self.widgets)})"


class State(TbModel):      # referred to in "default", the only object nested inside of States
    name: str
    root: bool
    layouts: Dict[str, Layout]
    # widgets: list   # skipping the step of going through widgets, this is the same as self.layouts["main"].widgets
    # index: str

    def __str__(self) -> str:
        return f"State ({self.index} {self.name})"


class Filter(TbModel):
    type: Optional[str]
    resolve_multiple: Optional[bool] = Field(alias="resolveMultiple")
    single_entity: Optional[Id] = Field(alias="singleEntity")
    entity_type: Optional[str] = Field(alias="entityType")
    entity_name_filter: Optional[str] = Field(alias="entityNameFilter")

    def __str__(self) -> str:
        return f"Filter ({self.type}, {self.single_entity.id})"


class EntityAlias(TbModel):
    id: str
    alias: str
    filter: Filter

    # index: str

    def __str__(self) -> str:
        return f"Entity Alias ({self.alias}, {self.id})"


class Setting(TbModel):
    state_controller_id: str = Field(alias="stateControllerId")
    show_title: bool = Field(alias="showTitle")
    show_dashboards_select: bool = Field(alias="showDashboardsSelect")
    show_entities_select: bool = Field(alias="showEntitiesSelect")
    show_dashboard_timewindow: bool = Field(alias="showDashboardTimewindow")
    show_dashboard_export: bool = Field(alias="showDashboardExport")
    toolbar_always_open: bool = Field(alias="toolbarAlwaysOpen")
    title_color: str = Field(alias="titleColor")

    def __str__(self) -> str:
        return f"Settings ({self.dict()})"


class RealTime(TbModel):
    interval: int
    time_window_ms: int = Field(alias="timewindowMs")

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Aggregation(TbModel):
    type: str
    limit: int

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class TimeWindow(TbModel):
    real_time: RealTime = Field(alias="realtime")
    aggregation: Aggregation

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Configuration(TbModel):
    widgets: Dict[str, Widget]
    states: Dict[str, State]
    entity_aliases: Dict[str, EntityAlias] = Field(alias="entityAliases")
    timewindow: TimeWindow
    settings: Setting
    # name: str

    def __str__(self) -> str:
        return f"Configuration"


class Dashboard(TbObject):
    id: Id
    created_time: datetime = Field(alias="createdTime")
    tenant_id: Id = Field(alias="tenantId")
    name: Optional[str]
    title: Optional[str]
    assigned_customers: List[CustomerId] = Field(alias="assignedCustomers")

    def __str__(self) -> str:
        return f"Dashboard ({self.name}, {self.title}, {self.id.id})"

    def is_public(self) -> bool:
        """
        Return True if dashboard is owned by the public user False otherwise
        """
        if self.assigned_customers is None:
            return False

        for c in self.assigned_customers:
            if c.public:
                return True

        return False


class DashboardDef(Dashboard):
    """ Extends Dashboard by adding a configuration. """
    configuration: Configuration

    def __str__(self) -> str:
        return f"Dashboard Definition ({self.name}, {self.title}, {self.id.id})"


class TbObjectType(Enum):
    dashboard = Dashboard
    customer = Customer
    device = Device


class TbApi:

    T = TypeVar("T")

    def tb_objects_from_list(self, json_list: List[str], object_type: Type[T]) -> List[T]:
        """ Given a list of json strings and a type, return a list of rehydrated objects of that type. """
        objects = []
        for jsn in json_list:
            objects.append(object_type(tbapi, **jsn))
        return objects


    MINUTES = 60

    def __init__(self, url: str, username: str, password: str, token_timeout=10 * MINUTES):
        self.mothership_url = url
        self.username = username
        self.password = password
        self.token_timeout = token_timeout  # In seconds

        self.token_time = 0
        self.token = None

        self.verbose = False
        self.public_user_id = None


    def get_token(self) -> str:
        """
        Fetches and return an access token needed by most other methods; caches tokens for reuse
        """
        # If we already have a valid token, use it
        if self.token is not None and time.time() - self.token_time < self.token_timeout:
            return self.token

        data = '{"username":"' + self.username + '", "password":"' + self.password + '"}'
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        # json = post("/api/auth/login", None, data, "Error requesting token")

        url = self.mothership_url + "/api/auth/login"
        response = requests.post(url, data=data, headers=headers)
        self.validate_response(response, "Error requesting token")

        self.token = json.loads(response.text)["token"]
        self.token_time = time.time()

        return self.token


    def get_users(self):
        """
        Return a list of all customers in the system
        """
        return self.get("/api/customers?limit=99999", "Error retrieving customers")["data"]


    def get_tenant_assets(self):
        """
        Returns a list of all assets for current tenant
        """
        return self.get("/api/tenant/assets?limit=99999", "Error retrieving assets for tenant")["data"]


    def get_tenant_devices(self):
        """
        Returns a list of all devices for current tenant
        """
        return self.get("/api/tenant/devices?limit=99999", "Error retrieving devices for tenant")["data"]


    # def get_customer_devices(self, cust):
    #     """
    #     Returns a list of all devices associated with a customer; pass in customer object or id
    #     """
    #     cust_id = self.get_id(cust)

    #     return self.get(f"/api/customer/{cust_id}/devices?limit=99999", f"Error retrieving devices for customer '{cust_id}'")["data"]


    def get_public_user_id(self) -> str:
        """
        Returns UUID of public customer, or None if there is none
        """
        if not self.public_user_id:
            self.public_user_id = self.get_user_uuid("Public")

        return self.public_user_id


    # TODO: ???
    def get_user_uuid(self, name):
        """
        Returns UUID of named customer, or None if user not found
        """
        return self.get_customer_by_name(name).id.id



    def add_customer(self, name, address, address2, city, state, zip, country, email, phone, additional_info=None):
        """
        Adds customer and returns JSON customer from database
        """
        data = {
            "title": name,
            "address": address,
            "address2": address2,
            "city": city,
            "state": state,
            "zip": zip,
            "country": country,
            "email": email,
            "phone": phone
        }

        if additional_info is not None:
            data["additionalInfo"] = additional_info

        return self.post("/api/customer", data, f"Error adding customer '{name}'")


    # def delete_customer_by_id(self, id):
    #     """
    #     Returns True if successful, False if the customer wasn't found
    #     """
    #     return self.delete(f"/api/customer/{id}", f"Error deleting customer '{id}'")


    # def delete_customer_by_name(self, name):
    #     """
    #     Returns True if successful, False if the customer wasn't found
    #     """
    #     id = self.get_user_uuid(name)
    #     if id is None:
    #         print(f"Could not find customer with name {name}")
    #         return False

    #     return self.delete_customer_by_id(id)


    # TODO: Move to Dashboard.assign_to_customer(Customer)
    def assign_dash_to_user(self, dash: Dashboard, customer: Customer):
        """
        Returns dashboard definition
        """
        dashboard_id = dash.id.id
        customer_id = customer.id.id
        return self.post(f"/api/customer/{customer_id}/dashboard/{dashboard_id}", None, f"Could not assign dashboard '{dashboard_id}' to customer '{customer_id}'")


    # TODO: Move to Dashboard.assign_to_public_user()   or   Dashboard.assign_to_customer(get_public_user())   ???
    def assign_dash_to_public_user(self, dash: Dashboard):
        """
        Pass in a dash or a dash_id
        """
        dash_id = dash.id.id
        return self.post(f"/api/customer/public/dashboard/{dash_id}", None, f"Error assigning dash '{dash_id}' to public customer")


    # TODO: Move to Dashboard.get_public_url()
    def get_public_dash_url(self, dash: Dashboard) -> Optional[str]:

        if not dash.is_public():
            return None

        dashboard_id = dash.id.id
        public_id = self.get_public_user_id()

        return f"{self.mothership_url}/dashboard/{dashboard_id}?publicId={public_id}"


    # TODO: Move to Dashboard.delete()
    def delete_dashboard(self, dash: Dashboard) -> bool:
        """
        Returns True if dashboard was deleted, False if it did not exist
        """
        dashboard_id = dash.id.id
        return self.delete(f"/api/dashboard/{dashboard_id}", f"Error deleting dashboard '{dashboard_id}'")


    # TODO: ???
    def create_dashboard_for_customer(self, dash_name, dash_def):
        """
        Returns dashboard definition
        """
        data = {
            "configuration": dash_def["configuration"],
            "title": dash_name,
            "name": dash_name
        }

        # Update the configuration
        return self.post("/api/dashboard", data, "Error creating new dashboard")


    # TODO: Move to Dashboard.save()
    def save_dashboard(self, dash_def):
        """
        Saves a fully formed dashboard definition
        """
        return self.post("/api/dashboard", dash_def, "Error saving dashboard")


    def get_dashboards_by_name(self, dash_name_prefix: str) -> List[Dashboard]:
        """
        Returns a list of all dashes starting with the specified name
        """
        objs = self.get(f"/api/tenant/dashboards?limit=99999&textSearch={dash_name_prefix}", f"Error retrieving dashboards starting with '{dash_name_prefix}'")["data"]

        dashes = list()

        for obj in objs:
            dashes.append(Dashboard(tbapi, **obj))

        return dashes


    def get_dashboard_by_name(self, dash_name: str) -> Optional[Dashboard]:
        """ Returns dashboard with specified name, or None if we can't find one """
        dashes = self.get_dashboards_by_name(dash_name)
        for dash in dashes:
            if dash.title == dash_name:
                return dash

        return None


    def get_dashboard_by_id(self, dash_id: Union[Id, str]) -> Dashboard:
        """
        Retrieve dashboard by id
        """
        if isinstance(dash_id, Id):
            dash_id = dash_id.id
        # otherwise, assume dash_id is a guid

        obj = self.get(f"/api/dashboard/info/{dash_id}", f"Error retrieving dashboard for '{dash_id}'")
        return Dashboard(self, **obj)


    # TODO: Move to Dashboard.get_definition()
    def get_dashboard_definition(self, dash_guid: Union[Id, str]) -> DashboardDef:
        obj = self.get(f"/api/dashboard/{dash_guid}", f"Error retrieving dashboard definition for '{dash_guid}'")
        return DashboardDef(tbapi, **obj)


    def get_customer_by_id(self, cust_id: Union[Id, str]) -> Customer:
        """
        Returns an instantiated Customer object cust_id can be either an Id object or a guid
        """
        if isinstance(cust_id, Id):
            cust_id = cust_id.id
        # otherwise, assume cust_id is a guid

        obj = self.get(f"/api/customer/{cust_id}", f"Could not retrieve Customer with id '{cust_id}'")
        return Customer(tbapi, **obj)


    def get_customers_by_name(self, cust_name_prefix: str) -> List[Customer]:
        """
        Returns a list of all customers starting with the specified name
        """
        obj = self.get(f"/api/customers?limit=99999&textSearch={cust_name_prefix}", f"Error retrieving customers with names starting with '{cust_name_prefix}'")["data"]
        x = self.tb_objects_from_list(obj, Customer)
        return x


    def get_customer_by_name(self, cust_name: str) -> Optional[Customer]:
        """
        Returns a customer with the specified name, or None if we can't find one
        """
        customers = self.get_customers_by_name(cust_name)
        return _exact_match(cust_name, customers)


    def get_all_customers(self) -> List[Customer]:
        obj = self.get("/api/customers?limit=99999", "Error fetching list of all customers")["data"]
        return self.tb_objects_from_list(obj, Customer)


    def get_device_by_id(self, device_id: str) -> Device:
        """
        Returns an instantiated Device object device_id can be either an Id object or a guid
        """
        if isinstance(device_id, Id):
            device_id = device_id.id
        # otherwise, assume device_id is a guid

        obj = self.get(f"/api/device/{device_id}", f"Could not retrieve Device with id '{device_id}'")
        return Device(self, **obj)


    def get_devices_by_name(self, device_name_prefix: str) -> List[Device]:
        """
        Returns a list of all devices starting with the specified name
        """
        data = self.get(f"/api/tenant/devices?limit=99999&textSearch={device_name_prefix}", f"Error fetching devices with name matching '{device_name_prefix}'")["data"]
        return self.tb_objects_from_list(data, Device)


    def get_device_by_name(self, device_name: str) -> Optional[Device]:
        """ Returns a device with the specified name, or None if we can't find one """
        devices = self.get_devices_by_name(device_name)
        return _exact_match(device_name, devices)


    def get_all_devices(self):
        json = self.get("/api/tenant/devices?limit=99999", "Error fetching list of all devices")["data"]
        return self.tb_objects_from_list(json, Device)

    # TODO: create Asset object
    def add_asset(self, asset_name, asset_type, shared_attributes, server_attributes):
        data = {
            "name": asset_name,
            "type": asset_type

        }
        asset = self.post("/api/asset", data, "Error adding asset")

        if server_attributes is not None:
            asset.set_server_attributes(server_attributes)

        if shared_attributes is not None:
            asset.set_shared_attributes(shared_attributes)

        return asset


    # TODO: Move to Device.new(tbapi,.....).save()?  # or not
    def add_device(self, device_name: str, device_type: str, shared_attributes: Optional[Dict[str, Any]] = None, server_attributes: Optional[Dict[str, Any]] = None): # -> Device: TODO: why won't python allow this??
        """
        Returns device object
        """
        data = {
            "name": device_name,
            "type": device_type,
        }
        device_json = self.post("/api/device", data, "Error adding device")

        device = Device(self, **device_json)

        if server_attributes is not None:
            device.set_server_attributes(server_attributes)

        if shared_attributes is not None:
            device.set_shared_attributes(shared_attributes)

        return device


    def get_asset_types(self):
        return self.get("/api/asset/types", "Error fetching list of all asset types")


    # def get_device_token(self, device):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     device_id = self.get_id(device)

    #     json = self.get(f"/api/device/{device_id}/credentials", f"Error retreiving device_key for device '{device_id}'")
    #     return json["credentialsId"]


    # def get_server_attributes(self, device):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.get_attributes(device, "SERVER_SCOPE")


    # def get_shared_attributes(self, device):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.get_attributes(device, "SHARED_SCOPE")


    # def get_client_attributes(self, device):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.get_attributes(device, "CLIENT_SCOPE")


    # def get_attributes(self, device, scope):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     device_id = self.get_id(device)

    #     return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/{scope}", f"Error retrieving {scope} attributes for '{device_id}'")


    # def set_server_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     attributes is a dict
    #     """
    #     return self.set_attributes(device, attributes, "SERVER_SCOPE")


    # def set_shared_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.set_attributes(device, attributes, "SHARED_SCOPE")


    # def set_client_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.set_attributes(device, attributes, "CLIENT_SCOPE")


    # def set_attributes_old(self, device, attributes, scope):
    #     device_id = self.get_id(device)
    #     return self.post(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}", attributes, f"Error setting {scope} attributes for device '{device}'")


    # def delete_server_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.delete_attributes(device, attributes, "SERVER_SCOPE")


    # def delete_shared_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.delete_attributes(device, attributes, "SHARED_SCOPE")


    # def delete_client_attributes(self, device, attributes):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     return self.delete_attributes(device, attributes, "CLIENT_SCOPE")


    # def delete_attributes(self, device, attributes, scope):
    #     """
    #     Pass an attribute name or a list of attributes
    #     """
    #     device_id = self.get_id(device)

    #     if type(attributes) is list or type(attributes) is tuple:
    #         attributes = ",".join(attributes)

    #     return self.delete(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}?keys={attributes}", f"Error deleting {scope} attributes for device '{device}'")


    # TODO: ???
    def send_asset_telemetry(self, asset_id, data, scope="SERVER_SCOPE", timestamp=None):
        if timestamp is not None:
            data = {"ts": timestamp, "values": data}
        return self.post(f"/api/plugins/telemetry/ASSET/{asset_id}/timeseries/{scope}", data, f"Error sending telemetry for asset with id '{asset_id}'")


    # def send_telemetry(self, device_token, data, timestamp=None):
    #     """
    #     Note that this requires the device's secret token, not the device_id!
    #     """
    #     if timestamp is not None:
    #         data = {"ts": timestamp, "values": data}
    #     return self.post(f"/api/v1/{device_token}/telemetry", data, f"Error sending telemetry for device with token '{device_token}'")


    # def get_telemetry_keys(self, device):
    #     device_id = self.get_id(device)

    #     return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries", f"Error retrieving telemetry keys for device '{device_id}'")


    # def get_latest_telemetry(self, device, telemetry_keys):
    #     """
    #     Pass a single key, a stringified comma-separate list, a list object, or a tuple
    #     """
    #     device_id = self.get_id(device)

    #     if isinstance(telemetry_keys, str):
    #         keys = telemetry_keys
    #     else:
    #         keys = ",".join(telemetry_keys)

    #     return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={keys}", f"Error retrieving latest telemetry for device '{device_id}' with keys '{keys}'")


    # def get_telemetry(self, device, telemetry_keys, startTime=None, endTime=None, interval=None, limit=None, agg=None):
    #     """
    #     Pass a single key, a stringified comma-separate list, a list object, or a tuple
    #     """
    #     device_id = self.get_id(device)

    #     if isinstance(telemetry_keys, str):
    #         keys = telemetry_keys
    #     else:
    #         keys = ",".join(telemetry_keys)

    #     if startTime is None:
    #         startTime = 0

    #     if endTime is None:
    #         endTime = int(time.time() * 1000)       # Unix timestamp, now, convert to milliseconds

    #     if interval is None:
    #         interval = 60 * 1000   # 1 minute, in ms

    #     if limit is None:
    #         limit = 100

    #     if agg is None:
    #         agg = "NONE"   # MIN, MAX, AVG, SUM, COUNT, NONE

    #     params = "/api/plugins/telemetry/DEVICE/" + device_id + "/values/timeseries?keys=" + keys + "&startTs=" + \
    #         str(int(startTime)) + "&endTs=" + str(int(endTime)) + "&interval=" + str(interval) + "&limit=" + str(limit) + "&agg=" + agg
    #     error_message = "Error retrieving telemetry for device '" + device_id + "' with date range '" + str(int(startTime)) + "-" + str(int(endTime)) + "' and keys '" + keys + "'"

    #     return self.get(params, error_message)


    # def delete_telemetry(self, device, key, timestamp):
    #     device_id = self.get_id(device)

    #     return self.delete(f"/api/plugins/telemetry/DEVICE/{device_id}/timeseries/values?key={key}&ts={str(int(timestamp))}", f"Error deleting telemetry for device '{device_id}'")


    # def is_public_device(self, device):
    #     """
    #     Return True if device is owned by the public user, False otherwise
    #     """
    #     pub_id = self.get_public_user_id()
    #     return self.get_id(device["customerId"]) == pub_id

    # get_id() has been moved to the TbObject class, for use in customer/device/dashboard.get_id()
    # it now exists as TbObject.get_id, and I will phase out the use of TbApi.get_id, below.
    # @staticmethod
    # def get_id(obj):
    #     """
    #     Works with Customers, Devices, Dashes
    #     """
    #     if obj is None:
    #         raise ValueError(f"Could not resolve id for 'None'")

    #     # If we were passed a string, assume it's already an id
    #     if isinstance(obj, str):
    #         return obj

    #     if "id" in obj and "id" in obj["id"]:
    #         return obj["id"]["id"]

    #     # This form is used when getting the id of a customer attached to a device... i.e. get_id(device["customerId"])
    #     if "id" in obj and isinstance(obj["id"], str):
    #         return obj["id"]

    #     # If dashboard is public, it will have a list of associated customers that follow this slightly different pattern
    #     if "customerId" in obj and "id" in obj["customerId"]:
    #         return obj["customerId"]["id"]

    #     raise ValueError(f"Could not resolve id for {obj}")


    # @staticmethod
    # def get_customer_from_device(device):
    #     return device["customerId"]["id"]


    # def assign_device_to_public_user(self, device):
    #     """
    #     Pass in a device or a device_id
    #     """
    #     device_id = self.get_id(device)

    #     return self.post(f"/api/customer/public/device/{device_id}", None, f"Error assigning device '{device_id}' to public customer")


    # TODO: ???
    def delete_asset(self, asset_id):
        """
        Returns True if asset was deleted, False if it did not exist
        """
        return self.delete(f"/api/asset/{asset_id}", f"Error deleting asset '{asset_id}'")


    # # TODO: Move to Device.delete()
    # def delete_device(self, device_id):
    #     """
    #     Returns True if device was deleted, False if it did not exist
    #     """
    #     return self.delete(f"/api/device/{device_id}", f"Error deleting device '{device_id}'")


    @staticmethod
    def pretty_print_request(req):
        print("{}\n{}\n{}\n\n{}".format("-----------START-----------", req.method + " " + req.url, "\n".join("{}: {}".format(k, v) for k, v in req.headers.items()), req.body, ))


    def add_auth_header(self, headers):
        """
        Modifies headers
        """
        token = self.get_token()
        if token is not None:
            headers["X-Authorization"] = "Bearer " + token


    def get(self, params, msg: str) -> Dict[str, Any]:
        url = self.mothership_url + params
        headers = {"Accept": "application/json"}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request("GET", url, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.get(url, headers=headers)
        self.validate_response(response, msg)

        return response.json()


    def delete(self, params, msg):
        url = self.mothership_url + params
        headers = {"Accept": "application/json"}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request("DELETE", url, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.delete(url, headers=headers)

        # Don't fail if not found
        if(response.status_code == HTTPStatus.NOT_FOUND):
            return False

        self.validate_response(response, msg)

        return True


    def post(self, params: str, data: Optional[Union[str, Dict[str, Any]]], msg: str) -> Dict[str, Any]:
        """
        Data can be a string or a dict; if it's a dict, it will be flattened
        """
        url = self.mothership_url + params
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.add_auth_header(headers)

        if self.verbose:
            if type(data) is dict:
                data = json.dumps(data)

            req = requests.Request("POST", url, json=data, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.post(url, json=data, headers=headers)
        self.validate_response(response, msg)

        if response.text is None or response.text == "":
            return {}

        return response.json()


    @staticmethod
    def validate_response(response, msg):
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            ex.args += (f"RESPONSE BODY: {response.content.decode('utf8')}",)        # Append our response to the exception to make it easier to figure out what went wrong
            raise

        except requests.exceptions.HTTPError:
            # if ex.response.status_code == 404:
            #     return None
            # else:
            #     raise ex
            # if "Invalid UUID string:" in ex.http_error_msg:
            #     return None
            return None

#####################################
# Tests



def get_birdhouses(tbapi):
    return tbapi.get_devices_by_name("Birdhouse")


def compare_dicts(d1, d2, path=""):
    for k in d1:
        if (k not in d2):
            print(path, ":")
            print(k + " as key not in d2", "\n")
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    path = path + "->" + k
                compare_dicts(d1[k], d2[k], path)
            else:
                if d1[k] != d2[k]:
                    print(path, ":")
                    print(" - ", k, " : ", d1[k])
                    print(" + ", k, " : ", d2[k])


# Get the secret stuff
from config import mothership_url, thingsboard_username, thingsboard_password
import json
from requests.exceptions import HTTPError

print("Loading data...", end=None)
tbapi = TbApi(mothership_url, thingsboard_username, thingsboard_password)

def get_test_device() -> Device:
    device = tbapi.get_device_by_name("Birdhouse 001")
    assert device
    return device


device = get_test_device()  # redundant (repeated below)
customer = tbapi.get_customer_by_name("Birdhouse 001")  # redundant (repeated below)
dash = tbapi.get_dashboard_by_name("Birdhouse 001 Dash")
dash_def = tbapi.get_dashboard_definition("0d538a70-d996-11e7-a394-bf47d8c29be7")

assert customer
assert dash

# Validate the EntityType enum
assert device.id.entity_type == EntityType.DEVICE.value
assert customer.id.entity_type == EntityType.CUSTOMER.value
assert dash.id.entity_type == EntityType.DASHBOARD.value
assert dash_def.id.entity_type == EntityType.DASHBOARD.value


try:
    bogus = tbapi.get_dashboard_definition("3d538a70-d996-11e7-a394-bf47d8c29be7")   # Bogus guid
    assert False
except HTTPError:
    pass

try:
    bogus = tbapi.get_dashboard_by_id("3d538a70-d996-11e7-a394-bf47d8c29be7")   # Bogus guid
    assert False
except HTTPError:
    pass

try:
    bogus = tbapi.get_customer_by_id("3d538a70-d996-11e7-a394-bf47d8c29be7")   # Bogus guid
    assert False
except HTTPError:
    pass



assert isinstance(tbapi.get_device_by_id(device.id.id), Device)     # Retrieve a device by its guid
assert isinstance(tbapi.get_device_by_id(device.id), Device)        # Retrieve a device by an Id object

try:
    bogus = tbapi.get_device_by_id("3d538a70-d996-11e7-a394-bf47d8c29be7")   # Bogus guid -> failure raises exception
    assert False
except HTTPError:
    pass

assert tbapi.get_device_by_name("Does Not Exist") is None   # Bogus name -> failure returns None

devices = tbapi.get_devices_by_name("Birdhouse 0")
assert len(devices) > 1
assert isinstance(devices[0], Device)

devices = tbapi.get_devices_by_name("Does Not Exist")
assert len(devices) == 0

devices = tbapi.get_all_devices()
assert len(devices) > 1
assert isinstance(devices[0], Device)

device = tbapi.get_device_by_name("Birdhouse 001")
assert isinstance(device, Device)
assert isinstance(device.id, Id)
token = device.get_token()
assert isinstance(token, str)
assert len(token) == 20     # Tokens are always 20 character strings

# Make sure these calls produce equivalent results
attrs1 = device.get_server_attributes()
attrs2 = device.get_attributes(AttributeScope.SERVER)
assert attrs1 == attrs2
assert len(attrs1) > 0

attrs1 = device.get_shared_attributes()
attrs2 = device.get_attributes(AttributeScope.SHARED)
assert attrs1 == attrs2
assert len(attrs1) > 0

attrs1 = device.get_client_attributes()
attrs2 = device.get_attributes(AttributeScope.CLIENT)
assert attrs1 == attrs2
assert len(attrs1) > 0

assert device.get_customer().id.entity_type == EntityType.CUSTOMER.value


# Set/retrieve/delete attributes
def test_attributes(device: Device, scope: AttributeScope):
    key = "test_delete_me"
    val = 12345

    # Verify key doesn't exist
    attrs = device.get_attributes(scope)
    assert key not in attrs # attrs.get(key) is None

    # Set
    device.set_attributes({key: val}, scope)
    attrs = device.get_attributes(scope)

    found = False
    for attr in attrs:
        if attr["key"] == key:
            assert attr["value"] == val
            found = True
    assert found

    # Cleanup
    found = False
    device.delete_attributes([key], scope)
    attrs = device.get_attributes(scope)
    for attr in attrs:
        if attr["key"] == key:
            assert attr["value"] == None
            found = True
    assert found == False


test_attributes(device, AttributeScope.SERVER)
test_attributes(device, AttributeScope.SHARED)
# test_attributes(device, AttributeScope.CLIENT) # TODO: should setting and getting in the Client scope work?

# Device ownership
device.assign_to(customer)
assert not device.is_public()
device = get_test_device()  # Get it again to make sure changes stuck
assert not device.is_public()

assert device.get_customer().id == customer.id
device.make_public()
assert device.is_public()
device = get_test_device()  # Get it again to make sure changes stuck
assert device.is_public()

assert device.get_customer().id != customer.id
device.assign_to(customer)
assert device.get_customer().id == customer.id
device = get_test_device()  # Get it again to make sure changes stuck
assert device.get_customer().id == customer.id

# Just make sure these work... more detailed tests below
assert device.get_telemetry_keys()
assert device.get_telemetry(device.get_telemetry_keys()[:3])

print(" done with first round of tests.")

print("testing devices round 2")

# create a new device
shared_attributes = {"my_shared_attribute_1": 111}
server_attributes = {"my_server_attribute_2": 222}
device = tbapi.add_device("Device Test Subject", "Guinea Pig", shared_attributes=shared_attributes, server_attributes=server_attributes)

assert(isinstance(device.get_customer(), str)) # should be a guid
token = device.get_token()
assert(isinstance(token, str))
assert(len(token) == 20)

# Customer tests
print("now testing customers")

customer = tbapi.get_customer_by_name("Birdhouse 001")

assert isinstance(customer, Customer)
assert isinstance(customer.id, Id)
assert tbapi.get_customer_by_id(customer.id.id) == customer
assert tbapi.get_customer_by_id(customer.id) == customer

assert tbapi.get_customer_by_name("Does Not Exist") is None

customers = tbapi.get_customers_by_name("Birdhouse 0")
assert len(customers) > 1
assert isinstance(customers[0], Customer)

customers = tbapi.get_customers_by_name("Does Not Exist")
assert len(customers) == 0

customers = tbapi.get_all_customers()
assert len(customers) > 1
assert isinstance(customers[0], Customer)


try:
    print(customer.additionalInfo)     # Should not be accessible -- we remapped this name
    assert False
except AttributeError:
    pass

# Assign an unknown attribute -- should raise exception
try:
    customer.unknown = "LLL"
    assert False
except ValueError:
    pass

# Assign an unknown attribute II -- should raise exception
try:
    customer["unknown"] = "LLL"
    assert False
except TypeError:
    pass

# Access an unknown attribute -- should raise exception
try:
    print(customer.unknown)
    assert False
except AttributeError:
    pass

# Access an unknown attribute II -- should raise exception
try:
    print(customer["strange"])
    assert False
except TypeError:
    pass


# Construct with an unknown attribute -- should raise exception
bad_cust_dict = customer.dict(by_alias=True)
bad_cust_dict["unknown_attr"] = 666
try:
    bad_c = Customer.from_dict(bad_cust_dict)
    assert False
except AttributeError:
    pass

# Time handled correctly (also verifies name translation: createdTime -> created_time -> createdTime)
assert(isinstance(customer.created_time, datetime))            # Rehydrated time is a datetime
assert(isinstance(json.loads(customer.json(by_alias=True))["createdTime"], int))     # Serialized time is int



# Dashboard built right?
assert type(dash.assigned_customers[0]) is CustomerId

# Check attribute renaming at top level -- incoming json uses createdTime, we remap to created_time.  Make sure it works.
assert dash.created_time
try:
    dash.createdTime
    assert False
except AttributeError:
    pass

# And check remapping when converting back to json
assert json.loads(dash.json(by_alias=True)).get("createdTime")
assert json.loads(dash.json(by_alias=True)).get("created_time") is None

# Check nested attribute renaming
assert dash.assigned_customers[0].customer_id.entity_type == EntityType.CUSTOMER.value
try:
    dash.assigned_customers[0].customer_id.entityType
    assert False
except AttributeError:
    pass
assert json.loads(dash.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entityType") == EntityType.CUSTOMER.value
assert json.loads(dash.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entity_type") is None

# assert(Device.from_dict(d.to_dict).to_dict == d.to_dict)


# Serialized looks like original?
# compare_dicts(dev_json, json.loads(d.json(by_alias=True)))


# Check GuidList[Id, Customer] ==> should fail

assert dash.is_public() is True



# Device telemetry tests -- TODO: make sure these clean up after themselves!
keys = ["datum_1", "datum_2"]
values = [555, 666]
timestamps = [1595897301 * 1000, 1595897302 * 1000] # second timestamp must be greater than first for check to work


expected_tel_keys = []
tel_keys = device.get_telemetry_keys()
assert(tel_keys == expected_tel_keys)


expected_telemetry = {}
expected_latest_telemetry = {}


def test_sending_telemetry(device: Device, data_index: int, timestamp_index: int):
    device.send_telemetry({keys[data_index]: values[data_index]}, timestamp=timestamps[timestamp_index])
    if keys[data_index] not in expected_tel_keys:
        expected_tel_keys.append(keys[data_index])
    tel_keys = device.get_telemetry_keys()
    assert(tel_keys == expected_tel_keys)

    if keys[data_index] not in expected_telemetry.keys():
        expected_telemetry[keys[data_index]]  = [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    else:
        expected_telemetry[keys[data_index]].insert(0, {"ts": timestamps[timestamp_index], "value": str(values[data_index])})
        # expected_telemetry[keys[data_index]] += [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    telemetry = device.get_telemetry(tel_keys)
    assert(telemetry == expected_telemetry)

    expected_latest_telemetry[keys[data_index]] = [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    latest_telemetry = device.get_latest_telemetry(tel_keys)
    assert(latest_telemetry == expected_latest_telemetry)


test_sending_telemetry(device, 0, 0)
test_sending_telemetry(device, 1, 0)
test_sending_telemetry(device, 0, 1)


# for tel_key in tel_keys:
#     for timestamp in timestamps:
#         device.delete_telemetry(tel_key, timestamp)
# telemetry = device.get_telemetry(tel_keys)
# assert(telemetry == {})



def check_attributes(device_attributes: List[Dict[str, Any]], expected_attributes: Dict[str, Any], expected=True):
    # device_attributes is a list of dicts, formatted [{"key": key, "lastUpdateTs": int, "value": val}]
    for expected_key, expected_val in expected_attributes.items():
        match: bool = False
        for attr in device_attributes: # a dict, formatted [{"key": key, "lastUpdateTs": int, "value": val}]
            if attr["key"] == expected_key and attr["value"] == expected_val:   # not checking the timestamps
                match = True
        assert(match == expected)


new_attributes = {"my_new_attribute_3": 333, "my_new_attribute_4": 444}
expected_attributes_for_shared_scope = {**shared_attributes, **new_attributes}

expected_attributes_for_server_scope = {**server_attributes, **new_attributes}

device.set_shared_attributes(new_attributes)
device.set_server_attributes(new_attributes)
check_attributes(device.get_shared_attributes(), expected_attributes_for_shared_scope, True)
check_attributes(device.get_server_attributes(), expected_attributes_for_server_scope, True)
device.delete_shared_attributes([*(expected_attributes_for_shared_scope.keys())])
device.delete_server_attributes([*(expected_attributes_for_server_scope.keys())])
check_attributes(device.get_shared_attributes(), expected_attributes_for_shared_scope, False)
check_attributes(device.get_server_attributes(), expected_attributes_for_server_scope, False)


device.set_attributes({**shared_attributes, **new_attributes}, AttributeScope.SHARED)
device.set_attributes({**server_attributes, **new_attributes}, AttributeScope.SERVER)
check_attributes(device.get_attributes(AttributeScope.SHARED), expected_attributes_for_shared_scope, True)
check_attributes(device.get_attributes(AttributeScope.SERVER), expected_attributes_for_server_scope, True)
device.delete_attributes([*(expected_attributes_for_shared_scope.keys())], AttributeScope.SHARED)
device.delete_attributes([*(expected_attributes_for_server_scope.keys())], AttributeScope.SERVER)
check_attributes(device.get_attributes(AttributeScope.SHARED), expected_attributes_for_shared_scope, False)
check_attributes(device.get_attributes(AttributeScope.SERVER), expected_attributes_for_server_scope, False)


device = device.assign_to_public_user()
assert(device.is_public())

device.delete()
try:
    test_sending_telemetry(device, token, 1, 1)
except requests.exceptions.HTTPError:
    print("the device has been successfully deleted!")


print("done testing devices round 2")
