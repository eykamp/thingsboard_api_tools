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
import json
import requests
import time
from http import HTTPStatus
from typing import  Optional, Dict, List, Any, Union, Type, TypeVar
from TbModel import Id

from Customer import Customer, CustomerId
from Dashboard import Dashboard, DashboardDef
from Device import Device, AttributeScope


MINUTES = 60

T = TypeVar("T")


class TbApi:

    def __init__(self, url: str, username: str, password: str, token_timeout: float = 10 * MINUTES):
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


    def get_tenant_assets(self):
        """
        Returns a list of all assets for current tenant
        """
        return self.get_paged("/api/tenant/assets", "Error retrieving assets for tenant")


    def get_tenant_devices(self):
        """
        Returns a list of all devices for current tenant
        """
        return self.get_paged("/api/tenant/devices", "Error retrieving devices for tenant")


    def get_public_user_id(self) -> CustomerId:
        """
        Returns Id of public customer, or None if there is none.  Caches value for future use.
        """
        if not self.public_user_id:
            public_customer = self.get_customer_by_name("Public")

            if not public_customer:
                raise Exception("Public customer is not defined in this Thingsboard instance!")     # Should never happen

            self.public_user_id = public_customer.customer_id

        return self.public_user_id


    def add_customer(self, name: str, address: str, address2: str, city: str, state: str, zip: str, country: str, email: str, phone: str, additional_info: Optional[Dict[str, Any]] = None) -> Customer:
        """
        Adds customer and returns JSON customer from database
        """

        from Customer import Customer

        data: Dict[str, Any] = {
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

        obj = self.post("/api/customer", data, f"Error adding customer '{name}'")

        if isinstance(obj["additionalInfo"], str):
            obj["additionalInfo"] = json.loads(obj["additionalInfo"])
            print(">>> Converting!")        # If we never see this, maybe we can delete this block?

        return Customer(self, **obj)


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


    def create_dashboard(self, dash_name: str, dash_def: "DashboardDef") -> "DashboardDef":
        """
        Returns DashboardDef
        """
        from Dashboard import DashboardDef

        data = {
            "configuration": dash_def.configuration.json(by_alias=True),
            "title": dash_name,
            "name": dash_name
        }

        # Update the configuration
        obj = self.post("/api/dashboard", data, "Error creating new dashboard")
        obj["configuration"] = json.loads(obj["configuration"])     # We need to hydrate this string for the parser to work
        return DashboardDef(self, **obj)


    def get_dashboards_by_name(self, dash_name_prefix: str) -> List[Dashboard]:
        """
        Returns a list of all dashes starting with the specified name
        """
        objs = self.get_paged(f"/api/tenant/dashboards?textSearch={dash_name_prefix}", f"Error retrieving dashboards starting with '{dash_name_prefix}'")

        dashes: List[Dashboard] = []

        for obj in objs:
            dashes.append(Dashboard(self, **obj))

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


    def get_customer_by_id(self, cust_id: Union[Id, str]) -> Customer:
        """
        Returns an instantiated Customer object cust_id can be either an Id object or a guid
        """
        if isinstance(cust_id, Id):
            cust_id = cust_id.id
        # otherwise, assume cust_id is a guid

        obj = self.get(f"/api/customer/{cust_id}", f"Could not retrieve Customer with id '{cust_id}'")
        return Customer(self, **obj)


    def get_customers_by_name(self, cust_name_prefix: str) -> List[Customer]:
        """
        Returns a list of all customers starting with the specified name
        """
        objs = self.get_paged(f"/api/customers?textSearch={cust_name_prefix}", f"Error retrieving customers with names starting with '{cust_name_prefix}'")

        objects: List[Customer] = []
        for obj in objs:
            # print(type(obj))
            print(obj)
            # o = json.loads(obj)
            print(type(obj["additionalInfo"]))

            # Sometimes this comes in as a dict, sometimes as a string.  Not sure why.
            if not isinstance(obj["additionalInfo"], dict):
                obj["additionalInfo"] = json.loads(obj["additionalInfo"])

            objects.append(Customer(self, **obj))
        return objects


    def get_customer_by_name(self, cust_name: str) -> Optional[Customer]:
        """
        Returns a customer with the specified name, or None if we can't find one
        """
        customers = self.get_customers_by_name(cust_name)
        return _exact_match(cust_name, customers)


    def get_all_customers(self) -> List[Customer]:
        """
        Return a list of all customers in the system
        """
        all_results = self.get_paged("/api/customers", "Error fetching list of all customers")
        return self.tb_objects_from_list(all_results, Customer)


    def get_device_by_id(self, device_id: Union[Id, str]) -> "Device":
        """
        Returns an instantiated Device object device_id can be either an Id object or a guid
        """
        if isinstance(device_id, Id):
            device_id = device_id.id
        # otherwise, assume device_id is a guid

        obj = self.get(f"/api/device/{device_id}", f"Could not retrieve Device with id '{device_id}'")
        return Device(self, **obj)


    def get_devices_by_name(self, device_name_prefix: str) -> List["Device"]:
        """
        Returns a list of all devices starting with the specified name
        """
        data = self.get_paged(f"/api/tenant/devices?textSearch={device_name_prefix}", f"Error fetching devices with name matching '{device_name_prefix}'")
        return self.tb_objects_from_list(data, Device)


    def get_device_by_name(self, device_name: str) -> Optional[Device]:
        """ Returns a device with the specified name, or None if we can't find one """
        devices = self.get_devices_by_name(device_name)
        return _exact_match(device_name, devices)


    def get_all_devices(self) -> List[Device]:
        all_results = self.get_paged(f"/api/tenant/devices", "Error fetching list of all devices")
        return self.tb_objects_from_list(all_results, Device)

    # TODO: create Asset object
    def add_asset(self, asset_name:str, asset_type:str, shared_attributes: Dict[str, Any], server_attributes: Dict[str, Any]):
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
    def add_device(self, device_name: str, device_type: str, shared_attributes: Optional[Dict[str, Any]] = None, server_attributes: Optional[Dict[str, Any]] = None) -> Device:
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
    def send_asset_telemetry(self, asset_id: str, data: Dict[str, Any], scope: AttributeScope = AttributeScope.SERVER, timestamp: Optional[int] = None):
        if timestamp is not None:
            data = {"ts": timestamp, "values": data}
        return self.post(f"/api/plugins/telemetry/ASSET/{asset_id}/timeseries/{scope.value}", data, f"Error sending telemetry for asset with id '{asset_id}'")


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
    def delete_asset(self, asset_id: str) -> bool:
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


    def tb_objects_from_list(self, json_list: List[Dict[str, Any]], object_type: Type[T]) -> List[T]:
        """ Given a list of json strings and a type, return a list of rehydrated objects of that type. """
        objects: List[T] = []
        for jsn in json_list:
            objects.append(object_type(self, **jsn))
        return objects


    @staticmethod
    def pretty_print_request(req: requests.PreparedRequest):
        print("{}\n{}\n{}\n\n{}".format("-----------START-----------", str(req.method) + " " + str(req.url), "\n".join("{}: {}".format(k, v) for k, v in req.headers.items()), req.body, ))


    def add_auth_header(self, headers: Dict[str, str]):
        """
        Modifies headers
        """
        token = self.get_token()
        if token is not None:
            headers["X-Authorization"] = "Bearer " + token



    def get_paged(self, params: str, msg: str) -> List[Dict[str, Any]]:
        page_size = 100
        all_results: List[Dict[str, Any]] = []
        page = 0

        if "?" in params:
            joiner = "&"
        else:
            joiner = "?"

        while True:
            results = self.get(f"{params}{joiner}page={page}&pageSize={page_size}", msg)["data"]
            if not results:
                break
            all_results += results

            if len(results) < page_size:        # This check will avoid an unnecessary round-trip 99% of the time... probably worth it
                break
            page += 1

        return all_results


    def get(self, params: str, msg: str) -> Any:            # List[Dict[str, Any]] ??
        if self.mothership_url is None:
            raise ConfigurationError("Cannot retrieve data without a URL: create a file called config.py and define 'mothership_url' to point to your Thingsboard server.\nExample: mothership_url = 'http://www.thingsboard.org:8080'")
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


    def delete(self, params: str, msg: str) -> bool:
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
        Data can be a string or a dict
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
    def validate_response(response: requests.Response, msg: str) -> None:
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as ex:
            ex.args += (msg, f"RESPONSE BODY: {response.content.decode('utf8')}")       # Append response to the exception to make it easier to diagnose
            raise

        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code != 404:
                ex.args += (msg, f"RESPONSE BODY: {response.content.decode('utf8')}")   # Append response to the exception to make it easier to diagnose
                raise


class ConfigurationError(Exception):
    pass


U = TypeVar("U", Customer, Device)

def _exact_match(name: str, object_list: List[U]) -> Optional[U]:
    matches: List[U] = []
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
