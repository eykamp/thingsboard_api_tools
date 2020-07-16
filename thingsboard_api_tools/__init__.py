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
from typing import  Optional, Dict, List, Any, Generic, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, Field
from devtools import debug


class TbApi:

    def __init__(self, url, username, password, token_timeout=600):  # 10 minutes
        self.mothership_url = url
        self.username = username
        self.password = password
        self.token_timeout = token_timeout  # In seconds

        self.token_time = 0
        self.token = None

        self.verbose = False


    def get_token(self):
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


    def get_customer(self, name):
        """
        Get customer with specified name
        """
        customers = self.get(f"/api/customers?limit=99999&textSearch={name}", f"Can't find customer with name '{name}'")
        for customer in customers["data"]:
            if(customer["title"] == name):
                return customer

        return None


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


    # TODO: Move to Customer.get_devices()
    def get_customer_devices(self, cust):
        """
        Returns a list of all devices associated with a customer; pass in customer object or id
        """
        cust_id = self.get_id(cust)

        return self.get(f"/api/customer/{cust_id}/devices?limit=99999", f"Error retrieving devices for customer '{cust_id}'")["data"]


    def get_public_user_id(self):
        """
        Returns UUID of public customer, or None if there is none
        """
        return self.get_user_uuid("Public")


    # TODO: ???
    def get_user_uuid(self, name):
        """
        Returns UUID of named customer, or None if user not found
        """
        return self.get_id(self.get_customer(name))


    def get_customer_by_id(self, cust_id):
        return self.get(f"/api/customer/{cust_id}", f"Could not retrieve customer with id '{cust_id}'")


    def get_customers_by_name(self, cust_name_prefix):
        """
        Returns a list of all customers starting with the specified name
        """
        return self.get(f"/api/customers?limit=99999&textSearch={cust_name_prefix}", f"Error retrieving customers with names starting with '{cust_name_prefix}'")["data"]


    def get_customer_by_name(self, cust_name):
        """
        Returns a customer with the specified name, or None if we can't find one
        """
        custs = self.get_customers_by_name(cust_name)
        for cust in custs:
            if cust["title"] == cust_name:
                return cust

        return None

    # TODO: Move to Customer.update()
    def update_customer(self, cust, name=None, address=None, address2=None, city=None, state=None, zip=None, country=None, email=None, phone=None, additional_info=None):
        """
        Updates an existing customer record --> pass in customer object, or a customer id additional_info is a dict
        """

        # Check if user passed a customer_id; if so, retrieve the customer object
        if isinstance(cust, str):
            cust = self.get_customer_by_id(cust)

        if name is not None:
            cust["title"] = name
        if address is not None:
            cust["address"] = address
        if address2 is not None:
            cust["address2"] = address2
        if city is not None:
            cust["city"] = city
        if state is not None:
            cust["state"] = state
        if zip is not None:
            cust["zip"] = zip
        if country is not None:
            cust["country"] = country
        if email is not None:
            cust["email"] = email
        if phone is not None:
            cust["phone"] = phone
        if additional_info is not None:
            cust["additionalInfo"] = additional_info

        return self.post("/api/customer", cust, "Error updating customer")


    # TODO: Move to Customer(tbapi, name, ....).save()  ??
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


    # TODO: Move to Customer.delete()
    def delete_customer_by_id(self, id):
        """
        Returns True if successful, False if the customer wasn't found
        """
        return self.delete(f"/api/customer/{id}", f"Error deleting customer '{id}'")


    # TODO: Move to Customer.delete()
    def delete_customer_by_name(self, name):
        """
        Returns True if successful, False if the customer wasn't found
        """
        id = self.get_user_uuid(name)
        if id is None:
            print(f"Could not find customer with name {name}")
            return False

        return self.delete_customer_by_id(id)


    # TODO: Move to Dashboard.assign_to_customer(Customer)
    def assign_dash_to_user(self, dash, customer):
        """
        Returns dashboard definition
        """
        dashboard_id = self.get_id(dash)
        customer_id = self.get_id(customer)
        return self.post(f"/api/customer/{customer_id}/dashboard/{dashboard_id}", None, f"Could not assign dashboard '{dashboard_id}' to customer '{customer_id}'")


    # TODO: Move to Customer.assign_to_public_user()   or   Custmer.assign_to_customer(get_public_user())   ???
    def assign_dash_to_public_user(self, dash):
        """
        Pass in a dash or a dash_id
        """
        dash_id = self.get_id(dash)
        return self.post(f"/api/customer/public/dashboard/{dash_id}", None, f"Error assigning dash '{dash_id}' to public customer")


    # TODO: Move to Dashboard.get_public_url()
    def get_public_dash_url(self, dash):

        if not self.is_public_dashboard(dash):
            return None

        dashboard_id = self.get_id(dash)
        public_id = self.get_public_user_id()

        return f"{self.mothership_url}/dashboard/{dashboard_id}?publicId={public_id}"


    # TODO: Move to Dashboard.delete()
    def delete_dashboard(self, dash):
        """
        Returns True if dashboard was deleted, False if it did not exist
        """
        dashboard_id = self.get_id(dash)
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


    def get_dashboards_by_name(self, dash_name_prefix):
        """
        Returns a list of all dashes starting with the specified name
        """
        return self.get(f"/api/tenant/dashboards?limit=99999&textSearch={dash_name_prefix}", f"Error retrieving dashboards starting with '{dash_name_prefix}'")["data"]


    def get_dashboard_by_name(self, dash_name):
        """
        Returns dashboard with specified name, or None if we can't find one
        """
        dashes = self.get_dashboards_by_name(dash_name)
        for dash in dashes:
            if dash['title'] == dash_name:
                return dash

        return None


    def get_dashboard_by_id(self, dash):
        """
        Retrieve dashboard by id
        """
        dash_id = self.get_id(dash)
        return self.get(f"/api/dashboard/info/{dash_id}", f"Error retrieving dashboard for '{dash_id}'")


    # TODO: Move to Dashboard.get_definition()
    def get_dashboard_definition(self, dash):
        dash_id = self.get_id(dash)
        return self.get(f"/api/dashboard/{dash_id}", f"Error retrieving dashboard definition for '{dash_id}'")


    def get_device_by_id(self, device_id):
        """
        Returns named device object, or None if it can't be found
        """
        if device_id is None:
            return None
        try:
            return self.get(f"/api/device/{device_id}", f"Could not retrieve device with id '{device_id}'")
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code == 404:
                return None
            else:
                raise ex


    def get_device_by_name(self, device_name):
        """
        Returns device object representing the first device found with the given name, or None if one can't be found
        """
        devices = self.get_devices_by_name(device_name)

        # Fine exact match
        for device in devices:
            if device["name"] == device_name:
                return device

        return None


    def get_devices_by_name(self, device_name_prefix):
        """
        Returns a list of all devices starting with the specified name
        """
        return self.get(f"/api/tenant/devices?limit=99999&textSearch={device_name_prefix}", f"Error fetching devices with name matching '{device_name_prefix}'")["data"]


    def get_all_devices(self):
        return self.get("/api/tenant/devices?limit=99999", "Error fetching list of all devices")["data"]


    # TODO: ???
    def add_asset(self, asset_name, asset_type, shared_attributes, server_attributes):
        data = {
            "name": asset_name,
            "type": asset_type

        }
        asset = self.post("/api/asset", data, "Error adding asset")
        asset_id = self.get_id(asset)

        if server_attributes is not None:
            self.set_server_attributes(asset_id, server_attributes)

        if shared_attributes is not None:
            self.set_shared_attributes(asset_id, shared_attributes)

        return asset


    # TODO: Move to Device.new(tbapi,.....).save()?
    def add_device(self, device_name, device_type, shared_attributes, server_attributes):
        """
        Returns device object
        """

        data = {
            "name": device_name,
            "type": device_type,
        }

        device = self.post("/api/device", data, "Error adding device")
        device_id = self.get_id(device)

        if server_attributes is not None:
            self.set_server_attributes(device_id, server_attributes)

        if shared_attributes is not None:
            self.set_shared_attributes(device_id, shared_attributes)

        return device


    def get_asset_types(self):
        return self.get("/api/asset/types", "Error fetching list of all asset types")


    # TODO: Move to Device.get_token()
    def get_device_token(self, device):
        """
        Pass in a device or a device_id
        """
        device_id = self.get_id(device)

        json = self.get(f"/api/device/{device_id}/credentials", f"Error retreiving device_key for device '{device_id}'")
        return json["credentialsId"]


    # TODO: Move to Device.get_server_attributes()
    def get_server_attributes(self, device):
        """
        Pass in a device or a device_id
        """
        return self.get_attributes(device, "SERVER_SCOPE")


    # TODO: Move to Device.get_shared_attributes()
    def get_shared_attributes(self, device):
        """
        Pass in a device or a device_id
        """
        return self.get_attributes(device, "SHARED_SCOPE")


    # TODO: Move to Device.get_client_attributes()
    def get_client_attributes(self, device):
        """
        Pass in a device or a device_id
        """
        return self.get_attributes(device, "CLIENT_SCOPE")


    # TODO: Move to Device.get_attributes(scope)
    def get_attributes(self, device, scope):
        """
        Pass in a device or a device_id
        """
        device_id = self.get_id(device)

        return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/{scope}", f"Error retrieving {scope} attributes for '{device_id}'")


    # TODO: Move to Device.get_server_attributes()
    def set_server_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        attributes is a dict
        """
        return self.set_attributes(device, attributes, "SERVER_SCOPE")


    # TODO: Move to Device.get_shared_attributes()
    def set_shared_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        """
        return self.set_attributes(device, attributes, "SHARED_SCOPE")


    # TODO: Move to Device.get_client_attributes()
    def set_client_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        """
        return self.set_attributes(device, attributes, "CLIENT_SCOPE")


    # TODO: Move to Device.set_attributes(attributes, scope)
    def set_attributes(self, device, attributes, scope):
        device_id = self.get_id(device)

        return self.post(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}", attributes, f"Error setting {scope} attributes for device '{device}'")


    # TODO: Move to Device.delete_server_attributes(attributes)
    def delete_server_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        """
        return self.delete_attributes(device, attributes, "SERVER_SCOPE")


    # TODO: Move to Device.delete_shared_attributes(attributes)
    def delete_shared_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        """
        return self.delete_attributes(device, attributes, "SHARED_SCOPE")


    # TODO: Move to Device.delete_client_attributes(attributes)
    def delete_client_attributes(self, device, attributes):
        """
        Pass in a device or a device_id
        """
        return self.delete_attributes(device, attributes, "CLIENT_SCOPE")


    # TODO: Move to Device.delete_attributes(attributes, scope)
    def delete_attributes(self, device, attributes, scope):
        """
        Pass an attribute name or a list of attributes
        """
        device_id = self.get_id(device)

        if type(attributes) is list or type(attributes) is tuple:
            attributes = ",".join(attributes)

        return self.delete(f"/api/plugins/telemetry/DEVICE/{device_id}/{scope}?keys={attributes}", f"Error deleting {scope} attributes for device '{device}'")


    # TODO: ???
    def send_asset_telemetry(self, asset_id, data, scope="SERVER_SCOPE", timestamp=None):
        if timestamp is not None:
            data = {"ts": timestamp, "values": data}
        return self.post(f"/api/plugins/telemetry/ASSET/{asset_id}/timeseries/{scope}", data, f"Error sending telemetry for asset with id '{asset_id}'")


    # TODO: Move to Device.send_telemetry(data, timestamp)
    def send_telemetry(self, device_token, data, timestamp=None):
        """
        Note that this requires the device's secret token, not the device_id!
        """
        if timestamp is not None:
            data = {"ts": timestamp, "values": data}
        return self.post(f"/api/v1/{device_token}/telemetry", data, f"Error sending telemetry for device with token '{device_token}'")


    # TODO: Move to Device.get_telementry_keys()
    def get_telemetry_keys(self, device):
        device_id = self.get_id(device)

        return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries", f"Error retrieving telemetry keys for device '{device_id}'")


    # TODO: Move to Device.get_latest_telemetry(telemetry_keys)
    def get_latest_telemetry(self, device, telemetry_keys):
        """
        Pass a single key, a stringified comma-separate list, a list object, or a tuple
        """
        device_id = self.get_id(device)

        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ",".join(telemetry_keys)

        return self.get(f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys={keys}", f"Error retrieving latest telemetry for device '{device_id}' with keys '{keys}'")


    # TODO: Move to Device.get_telemetry(...)
    def get_telemetry(self, device, telemetry_keys, startTime=None, endTime=None, interval=None, limit=None, agg=None):
        """
        Pass a single key, a stringified comma-separate list, a list object, or a tuple
        """
        device_id = self.get_id(device)

        if isinstance(telemetry_keys, str):
            keys = telemetry_keys
        else:
            keys = ",".join(telemetry_keys)

        if startTime is None:
            startTime = 0

        if endTime is None:
            endTime = int(time.time() * 1000)       # Unix timestamp, now, convert to milliseconds

        if interval is None:
            interval = 60 * 1000   # 1 minute, in ms

        if limit is None:
            limit = 100

        if agg is None:
            agg = "NONE"   # MIN, MAX, AVG, SUM, COUNT, NONE

        params = "/api/plugins/telemetry/DEVICE/" + device_id + "/values/timeseries?keys=" + keys + "&startTs=" + \
            str(int(startTime)) + "&endTs=" + str(int(endTime)) + "&interval=" + str(interval) + "&limit=" + str(limit) + "&agg=" + agg
        error_message = "Error retrieving telemetry for device '" + device_id + "' with date range '" + str(int(startTime)) + "-" + str(int(endTime)) + "' and keys '" + keys + "'"

        return self.get(params, error_message)


    # TODO: Move to Device.delete_telemetry(key, timestamp)
    def delete_telemetry(self, device, key, timestamp):
        device_id = self.get_id(device)

        return self.delete(f"/api/plugins/telemetry/DEVICE/{device_id}/timeseries/values?key={key}&ts={str(int(timestamp))}", f"Error deleting telemetry for device '{device_id}'")


    # TODO: Move to Device.is_public()
    def is_public_device(self, device):
        """
        Return True if device is owned by the public user, False otherwise
        """
        pub_id = self.get_public_user_id()
        return self.get_id(device["customerId"]) == pub_id


    @staticmethod
    def get_id(obj):
        """
        Works with Customers, Devices, Dashes
        """
        if obj is None:
            raise ValueError(f"Could not resolve id for 'None'")

        # If we were passed a string, assume it's already an id
        if isinstance(obj, str):
            return obj

        if "id" in obj and "id" in obj["id"]:
            return obj["id"]["id"]

        # This form is used when getting the id of a customer attached to a device... i.e. get_id(device["customerId"])
        if "id" in obj and isinstance(obj["id"], str):
            return obj["id"]

        # If dashboard is public, it will have a list of associated customers that follow this slightly different pattern
        if "customerId" in obj and "id" in obj["customerId"]:
            return obj["customerId"]["id"]

        raise ValueError(f"Could not resolve id for {obj}")


    # TODO: Move to Device.get_customer()
    @staticmethod
    def get_customer_from_device(device):
        return device["customerId"]["id"]


    # TODO: Move to Device.assign_to_public_user()
    def assign_device_to_public_user(self, device):
        """
        Pass in a device or a device_id
        """
        device_id = self.get_id(device)

        return self.post(f"/api/customer/public/device/{device_id}", None, f"Error assigning device '{device_id}' to public customer")


    # TODO: ???
    def delete_asset(self, asset_id):
        """
        Returns True if asset was deleted, False if it did not exist
        """
        return self.delete(f"/api/asset/{asset_id}", f"Error deleting asset '{asset_id}'")


    # TODO: Move to Device.delete()
    def delete_device(self, device_id):
        """
        Returns True if device was deleted, False if it did not exist
        """
        return self.delete(f"/api/device/{device_id}", f"Error deleting device '{device_id}'")


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


    def get(self, params, msg):
        url = self.mothership_url + params
        headers = {"Accept": "application/json"}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request("GET", url, headers=headers)
            prepared = req.prepare()
            TbApi.pretty_print_request(prepared)

        response = requests.get(url, headers=headers)
        self.validate_response(response, msg)

        return json.loads(response.text)


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


    def post(self, params, data, msg):
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
            ex.args += (f"RESPONSE BODY: {response.content.decode('utf8')}",)        # Append our response to the exception to make it easier to figure out WTF went wrong
            raise




class TbObject(BaseModel):
    class Config:
        json_encoders = {
            datetime: lambda v: int(v.timestamp() * 1000),  # TB expresses datetimes as epochs in milliseonds
        }

    def __repr__(self) -> str:
        return self.__str__()


class Id(TbObject):
    id: str
    entity_type: Optional[str] = Field(alias="entityType")

    def __str__(self) -> str:
        return f"Id ({self.entity_type}, {self.id})"


class Device(TbObject):
    id: Id
    additional_info: Optional[str] = Field(alias="additionalInfo")
    tenant_id: Id = Field(alias="tenantId")
    customer_id: Id = Field(alias="customerId")
    name: Optional[str]
    type: Optional[str]
    label: Optional[str]
    created_time: datetime = Field(alias="createdTime")


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
    # customer_id: Id = Field(alias="customerId")
    # public: bool

    def __str__(self) -> str:
        return "Customer (" + str(self.title) + ", " + str(self.id.id) + ")"

    def is_public(self) -> bool:
        if not self.additional_info:
            return False
        # else
        return self.additional_info.get("isPublic", False)

class CustomerId(TbObject):
    customer_id: Id = Field(alias="customerId")
    public: bool
    title: str

    def __str__(self) -> str:
        return f"CustomerId ({self.title}, {self.customer_id.id})"


class Widget(TbObject):
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


class SubWidget(TbObject):      # used within States <- Layouts <- Main <- Widgets
    size_x: int = Field(alias="sizeX")
    size_y: int = Field(alias="sizeY")
    mobile_height: Optional[int] = Field(alias="mobileHeight")
    row: int
    col: int
    # index: str

    def __str__(self) -> str:
        return f"SubWidget ({self.index})"


class GridSetting(TbObject):        # used within States <- Layouts <- Main <- GridSetting
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


class Layout(TbObject):      # used within States <- Layouts <- Main <- Widgets
    widgets: Dict[str, SubWidget]
    grid_settings: GridSetting = Field(alias="gridSettings")
    # index: str          # new name of the layout

    def __str__(self) -> str:
        return f"Layout ({len(self.widgets)})"


class State(TbObject):      # referred to in "default", the only object nested inside of States
    name: str
    root: bool
    layouts: Dict[str, Layout]
    # widgets: list   # skipping the step of going through widgets, this is the same as self.layouts["main"].widgets
    # index: str

    def __str__(self) -> str:
        return f"State ({self.index} {self.name})"


class Filter(TbObject):
    type: Optional[str]
    resolve_multiple: Optional[bool] = Field(alias="resolveMultiple")
    single_entity: Optional[Id] = Field(alias="singleEntity")
    entity_type: Optional[str] = Field(alias="entityType")
    entity_name_filter: Optional[str] = Field(alias="entityNameFilter")

    def __str__(self) -> str:
        return f"Filter ({self.type}, {self.single_entity.id})"


class EntityAlias(TbObject):
    id: str
    alias: str
    filter: Filter

    # index: str

    def __str__(self) -> str:
        return f"Entity Alias ({self.alias}, {self.id})"


class Setting(TbObject):
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


class RealTime(TbObject):
    interval: int
    time_window_ms: int = Field(alias="timewindowMs")

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Aggregation(TbObject):
    type: str
    limit: int

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class TimeWindow(TbObject):
    real_time: RealTime = Field(alias="realtime")
    aggregation: Aggregation

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Configuration(TbObject):
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

    def is_public(self):
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


#####################################
# Tests

import json

def get_birdhouses(tbapi):
    return tbapi.get_devices_by_name("Birdhouse")

def compare_dicts(d1, d2, path=""):
    for k in d1:
        if (k not in d2):
            print (path, ":")
            print (k + " as key not in d2", "\n")
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    path = path + "->" + k
                compare_dicts(d1[k], d2[k], path)
            else:
                if d1[k] != d2[k]:
                    print (path, ":")
                    print (" - ", k," : ", d1[k])
                    print (" + ", k," : ", d2[k])



# Get the secret stuff
from config import mothership_url, thingsboard_username, thingsboard_password

print("Loading data...", end=None)
tbapi = TbApi(mothership_url, thingsboard_username, thingsboard_password)

dev_json = tbapi.get_device_by_name("Birdhouse 181")
cust_json = tbapi.get_customer("Birdhouse 181")
dash_json = tbapi.get_dashboard_by_name("Birdhouse 001 Dash")
dash_def_json = tbapi.get_dashboard_definition("0d538a70-d996-11e7-a394-bf47d8c29be7")

print(" done.")

id = Id(**{"id": "12345", "entity_type": "TEST"})

print(id)
d = Device(**dev_json)
c = Customer(**cust_json)


# debug(dash_def_json)
dash = Dashboard.parse_obj(dash_json)
dash_def = DashboardDef.parse_obj(dash_def_json)


try:
    print(c.additionalInfo)     # Should not be accessible -- we remapped this name
    assert(False)
except AttributeError:
    pass



# Assign an unknown attribute -- should raise exception
try:
    c.unknown = "LLL"
    assert(False)
except ValueError:
    pass

# Assign an unknown attribute II -- should raise exception
try:
    c["unknown"] = "LLL"
    assert(False)
except TypeError:
    pass

# Access an unknown attribute -- should raise exception
try:
    print(c.unknown)
    assert(False)
except AttributeError:
    pass

# Access an unknown attribute II -- should raise exception
try:
    print(c["strange"])
    assert(False)
except TypeError:
    pass


# Construct with an unknown attribute -- should raise exception
bad_cust_json = cust_json.copy()
bad_cust_json["unknown_attr"] = 666
try:
    bad_c = Customer.from_dict(bad_cust_json)
    assert(False)
except AttributeError:
    pass

# Time handled correctly (also verifies name translation: createdTime -> created_time -> createdTime)
assert(isinstance(c.created_time, datetime))            # Rehydrated time is a datetime
assert(isinstance(json.loads(c.json(by_alias=True))["createdTime"], int))     # Serialized time is int


# Dashboard built right?
assert(type(dash.assigned_customers[0]) is CustomerId)

# Check attribute renaming at top level
assert(d.created_time)
try:
    d.createdTime
    assert(False)
except AttributeError:
    pass
assert(json.loads(d.json(by_alias=True)).get("createdTime"))
assert(json.loads(d.json(by_alias=True)).get("created_time") is None)

# Check nested attribute renaming
assert(d.customer_id.entity_type)
try:
    d.customer_id.entityType
    assert(False)
except AttributeError:
    pass
assert(json.loads(d.json(by_alias=True)).get("customerId", {}).get("entityType"))
assert(json.loads(d.json(by_alias=True)).get("customerId", {}).get("entity_type") is None)

# assert(Device.from_dict(d.to_dict).to_dict == d.to_dict)


# Serialized looks like original?
compare_dicts(dev_json, json.loads(d.json(by_alias=True)))


# Check GuidList[Id, Customer] ==> should fail

assert(dash.is_public() is True)

pass
