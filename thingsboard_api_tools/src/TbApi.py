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

from typing import  Optional, Dict, List, Any, Union, Type, TypeVar, TYPE_CHECKING

import json as Json
import requests
import time
from http import HTTPStatus

if TYPE_CHECKING:
    from .models.Customer import Customer, CustomerId
    from .models.Dashboard import Dashboard
    from .models.Device import Device
    from .models.DeviceProfile import DeviceProfile, DeviceProfileInfo
    from .models.TbModel import Id, TbObject

MINUTES = 60


T = TypeVar("T", bound="TbObject")      # T can be any subclass of TbObject

class TbApi:
    NULL_GUID = "13814000-1dd2-11b2-8080-808080808080"      # From EntityId.java in TB codebase

    def __init__(self, url: str, username: str, password: str, token_timeout: float = 10 * MINUTES):
        self.mothership_url: str = url
        self.username: str = username
        self.password: str = password
        self.token_timeout: float = token_timeout  # In seconds (epoch time, actually)

        self.token_time: float = 0
        self.token: str | None = None

        self.verbose: bool = False
        self.public_user_id: "CustomerId | None" = None


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
        try:
            response = requests.post(url, data=data, headers=headers)
        except requests.ConnectTimeout as ex:
            ex.args = (f"Could not connect to server (url='{url}').  Is it up?", *ex.args)
            raise


        self.validate_response(response, "Error requesting token")

        self.token = Json.loads(response.text)["token"]
        if not self.token:
            raise TokenError("No token received from server")

        self.token_time = time.time()

        return self.token


    def get_tenant_assets(self):
        """
        Returns a list of all assets for current tenant
        """
        return self.get_paged("/api/tenant/assets", "Error retrieving assets for tenant")


    def get_tenant_devices(self):
        """
        Returns a list of all ecustdevices for current tenant
        """
        return self.get_paged("/api/tenant/devices", "Error retrieving devices for tenant")


    def get_public_user_id(self):
        """
        Returns Id of public customer, or None if there is none.  Caches value for future use.
        """
        if not self.public_user_id:
            public_customer = self.get_customer_by_name("Public")

            if not public_customer:
                # This could happen if nothing has been yet set to public
                return None

            self.public_user_id = public_customer.customer_id

        return self.public_user_id


    def create_dashboard(self, name: str, template: Optional["Dashboard"] = None, id: Optional["Id"] = None):
        """
        Returns a Dashboard (including configuration)
        """

        from .models.Dashboard import Dashboard

        data: dict[str, Any] = {
            "title": name,
        }

        if template and template.configuration:
            data["configuration"] = template.configuration.model_dump(by_alias=True)

        if id:
            data["id"] = id.model_dump(by_alias=True)

        # Update the configuration
        obj = self.post("/api/dashboard", data, "Error creating new dashboard")
        return Dashboard(tbapi=self, **obj)


    def get_all_dashboard_headers(self):
        """
        Return a list of all dashboards in the system
        """
        from .models.Dashboard import DashboardHeader

        all_results = self.get_paged("/api/tenant/dashboards", "Error fetching list of all dashboards")
        return self.tb_objects_from_list(all_results, DashboardHeader)


    def get_dashboard_headers_by_name(self, dash_name_prefix: str):
        """
        Returns a list of all dashes starting with the specified name
        """

        from .models.Dashboard import DashboardHeader

        url = f"/api/tenant/dashboards?textSearch={dash_name_prefix}"
        objs = self.get_paged(url, f"Error retrieving dashboards starting with '{dash_name_prefix}'")

        dashes: List[DashboardHeader] = []

        for obj in objs:
            dashes.append(DashboardHeader(tbapi=self, **obj))

        return dashes


    def get_dashboard_by_name(self, dash_name: str) -> Optional["Dashboard"]:
        """ Returns dashboard with specified name, or None if we can't find one """
        headers = self.get_dashboard_headers_by_name(dash_name)
        for header in headers:
            if header.name == dash_name:
                return header.get_dashboard()

        return None


    def get_dashboard_by_id(self, dash_id: Union["Id", str]):
        return self.get_dashboard_header_by_id(dash_id).get_dashboard()


    def get_dashboard_header_by_id(self, dash_id: Union["Id", str]):
        """
        Retrieve dashboard by id
        """
        from .models.Dashboard import DashboardHeader
        from .models.TbModel import Id

        if isinstance(dash_id, Id):
            dash_id = dash_id.id
        # otherwise, assume dash_id is a guid

        obj = self.get(f"/api/dashboard/info/{dash_id}", f"Error retrieving dashboard for '{dash_id}'")
        return DashboardHeader(tbapi=self, **obj)


    def create_customer(
        self,
        name: str,
        # tenant_id: Id,            # Appears unsupported?  Can be omitted.
        address: Optional[str] = None,
        address2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip: Optional[str] = None,
        country: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        additional_info: dict[str, Any] = {},
        server_attributes: dict[str, Any] = {},
    ):
        """ Factory method. """
        from .models.Customer import Customer

        data: dict[str, Any] = {
            "title": name,
            # "tenantId": tenant_id.model_dump(),       # Can't get this to work
            "address": address,
            "address2": address2,
            "city": city,
            "state": state,
            "zip": zip,
            "country": country,
            "email": email,
            "phone": phone,
            "additionalInfo": additional_info,
        }

        obj = self.post("/api/customer", Json.dumps(data), "Error creating customer")
        customer = Customer(tbapi=self, **obj)

        if server_attributes:
            customer.set_server_attributes(server_attributes)

        return customer


    def get_customer_by_id(self, cust_id: Union["CustomerId", "Id", str]):
        """
        Returns an instantiated Customer object cust_id can be either an Id object or a guid.  If the passed id is the NULL_GUID,
        return None.
        """
        from .models.Customer import Customer, CustomerId
        from .models.TbModel import Id

        if isinstance(cust_id, CustomerId):
            cust_id = cust_id.id.id
        elif isinstance(cust_id, Id):
            cust_id = cust_id.id
        # otherwise, assume cust_id is a guid

        if cust_id == TbApi.NULL_GUID:
            return None

        obj = self.get(f"/api/customer/{cust_id}", f"Could not retrieve Customer with id '{cust_id}'")
        return Customer(tbapi=self, **obj)


    def get_customers_by_name(self, cust_name_prefix: str):
        """
        Returns a list of all customers starting with the specified name
        """
        from .models.Customer import Customer

        cust_datas = self.get_paged(f"/api/customers?textSearch={cust_name_prefix}", f"Error retrieving customers with names starting with '{cust_name_prefix}'")

        customers: List[Customer] = []
        for cust_data in cust_datas:
            # Sometimes this comes in as a dict, sometimes as a string.  Not sure why.
            if cust_data["additionalInfo"] is not None and not isinstance(cust_data["additionalInfo"], dict):
                cust_data["additionalInfo"] = Json.loads(cust_data["additionalInfo"])

            customers.append(Customer(tbapi=self, **cust_data))
        return customers


    def get_customer_by_name(self, cust_name: str):
        """
        Returns a customer with the specified name, or None if we can't find one
        """
        customers = self.get_customers_by_name(cust_name)
        return _exact_match(cust_name, customers)


    def get_all_customers(self):
        """
        Return a list of all customers in the system
        """
        from .models.Customer import Customer

        all_results = self.get_paged("/api/customers", "Error fetching list of all customers")
        return self.tb_objects_from_list(all_results, Customer)


    def get_all_tenants(self):
        """
        Return a list of all tenants in the system
        """
        from .models.Tenant import Tenant

        all_results = self.get_paged("/api/tenants", "Error fetching list of all tenants")
        return self.tb_objects_from_list(all_results, Tenant)


    def create_device(
        self,
        name: Optional[str],
        type: Optional[str] = None,     # Use this to assign device to a profile?
        label: Optional[str] = None,
        # device_profile_id: Id,        # Can't make this work
        # software_id: Optional[Id],    # Can't make this work -- probably done via another endpoint
        # firmware_id: Optional[Id],    # Can't make this work -- probably done via another endpoint
        additional_info: Optional[Dict[str, Any]] = None,
        customer: Optional["Customer"] = None,
        shared_attributes: Optional[Dict[str, Any]] = None,
        server_attributes: Optional[Dict[str, Any]] = None,
    ):
        """ Factory method. """

        from .models.Device import Device

        data: Dict[str, Any] = {
            "name": name,
            "label": label,
            "type": type,
            "additionalInfo": additional_info,
        }

        device_json = self.post("/api/device", data, "Error creating new device")
        # https://demo.thingsboard.io/swagger-ui.html#/device-controller/saveDeviceUsingPOST

        device = Device(tbapi=self, **device_json)

        if customer:
            device.assign_to(customer)

        if server_attributes is not None:
            device.set_server_attributes(server_attributes)

        if shared_attributes is not None:
            device.set_shared_attributes(shared_attributes)

        return device



    def get_device_by_id(self, device_id: Union["Id", str]):
        """
        Returns an instantiated Device object device_id can be either an Id object or a guid
        """
        from .models.TbModel import Id
        from .models.Device import Device

        if isinstance(device_id, Id):
            device_id = device_id.id
        # otherwise, assume device_id is a guid

        obj = self.get(f"/api/device/{device_id}", f"Could not retrieve Device with id '{device_id}'")

        # This hack is to fix a bug in TB 3.2 (and probably earlier) where customer_id comes back with NULL_GUID
        if obj["customerId"]["id"] == TbApi.NULL_GUID:
            device = self.get_device_by_name(obj["name"])
            assert device
            return device

        return Device(self, **obj)


    def get_devices_by_name(self, device_name_prefix: str):
        """
        Returns a list of all devices starting with the specified name
        """
        from .models.Device import Device

        data = self.get_paged(f"/api/tenant/devices?textSearch={device_name_prefix}", f"Error fetching devices with name matching '{device_name_prefix}'")
        return self.tb_objects_from_list(data, Device)


    def get_device_by_name(self, device_name: str | None):
        """ Returns a device with the specified name, or None if we can't find one """
        if device_name is None:     # Occasionally helpful
            return None
        devices = self.get_devices_by_name(device_name)
        return _exact_match(device_name, devices)


    def get_devices_by_type(self, device_type: str):
        from .models.Device import Device

        data = self.get(f"/api/tenant/devices?pageSize=99999&page=0&type={device_type}", f"Error fetching devices with type '{device_type}'")["data"]
        return self.tb_objects_from_list(data, Device)


    def get_all_devices(self):
        from .models.Device import Device

        all_results = self.get_paged("/api/tenant/devices", "Error fetching list of all Devices")
        return self.tb_objects_from_list(all_results, Device)


    def get_all_device_profiles(self):
        from .models.Device import DeviceProfile

        all_results = self.get_paged("/api/deviceProfiles", "Error fetching list of all DeviceProfiles")
        return self.tb_objects_from_list(all_results, DeviceProfile)


    def get_device_profile_by_id(self, device_profile_id: Union["Id", str]):
        """
        Returns an instantiated DeviceProfile object
        device_profile_id can be either an Id object or a guid
        """
        from .models.DeviceProfile import DeviceProfile
        from .models.TbModel import Id

        if isinstance(device_profile_id, Id):
            device_profile_id = device_profile_id.id
        # otherwise, assume device_profile_id is a guid

        obj = self.get(f"/api/deviceProfile/{device_profile_id}", f"Could not retrieve DeviceProfile with id '{device_profile_id}'")

        return DeviceProfile(tbapi=self, **obj)


    def get_device_profiles_by_name(self, device_profile_name_prefix: str):
        """
        Returns a list of all DeviceProfiles starting with the specified name
        """
        from .models.DeviceProfile import DeviceProfile

        data = self.get_paged(f"/api/deviceProfiles?textSearch={device_profile_name_prefix}", f"Error fetching DeviceProfiles with name matching '{device_profile_name_prefix}'")
        return self.tb_objects_from_list(data, DeviceProfile)


    def get_device_profile_by_name(self, device_profile_name: str):
        """ Returns a DeviceProfile with the specified name, or None if we can't find one """
        device_profiles = self.get_device_profiles_by_name(device_profile_name)
        return _exact_match(device_profile_name, device_profiles)


    def get_all_device_profile_infos(self):
        from .models.DeviceProfile import DeviceProfileInfo

        all_results = self.get_paged("/api/deviceProfileInfos", "Error fetching list of all DeviceProfileInfos")
        return self.tb_objects_from_list(all_results, DeviceProfileInfo)


    def get_device_profile_info_by_id(self, device_profile_info_id: Union["Id", str]):
        """
        Returns an instantiated DeviceProfileInfo object
        device_profile_info_id can be either an Id object or a guid
        """
        from .models.DeviceProfile import DeviceProfileInfo
        from .models.TbModel import Id

        if isinstance(device_profile_info_id, Id):
            device_profile_info_id = device_profile_info_id.id
        # otherwise, assume device_profile_info_id is a guid

        obj = self.get(f"/api/deviceProfileInfo/{device_profile_info_id}", f"Could not retrieve DeviceProfileInfo with id '{device_profile_info_id}'")

        return DeviceProfileInfo(tbapi=self, **obj)


    def get_device_profile_infos_by_name(self, device_profile_info_name_prefix: str):
        """
        Returns a list of all DeviceProfileInfos starting with the specified name
        """
        from .models.DeviceProfile import DeviceProfileInfo

        data = self.get_paged(f"/api/deviceProfileInfos?textSearch={device_profile_info_name_prefix}", f"Error fetching DeviceProfileInfos with name matching '{device_profile_info_name_prefix}'")
        return self.tb_objects_from_list(data, DeviceProfileInfo)


    def get_device_profile_info_by_name(self, device_profile_info_name: str):
        """ Returns a DeviceProfileInfo with the specified name, or None if we can't find one """
        device_profile_infos = self.get_device_profile_infos_by_name(device_profile_info_name)
        return _exact_match(device_profile_info_name, device_profile_infos)


    # TODO: create Asset object
    def add_asset(self, asset_name:str, asset_type:str, shared_attributes: Dict[str, Any] | None, server_attributes: Dict[str, Any] | None):
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


    def get_asset_types(self):
        return self.get("/api/asset/types", "Error fetching list of all asset types")


    def get_current_user(self):
        """ Gets info about the user whose credentials are running this API. """
        from .models.User import User

        obj: Dict[str, Any] = self.get_paged("/api/users", "Error fetching info about current user")[0]
        return User(tbapi=self, **obj)


    def get_current_tenant_id(self):
        return self.get_current_user().tenant_id


    def tb_objects_from_list(self, json_list: List[Dict[str, Any]], object_type: Type[T]) -> list[T]:
        """ Given a list of json strings and a type, return a list of rehydrated objects of that type. """
        objects: List[T] = []
        for jsn in json_list:
            objects.append(object_type(tbapi=self, **jsn))
        return objects


    # based off https://stackoverflow.com/questions/20658572/python-requests-print-entire-http-request-raw
    @staticmethod
    def pretty_print_request(request: Union[requests.PreparedRequest, requests.Request]):
        request = request.prepare() if isinstance(request, requests.Request) else request

        headers = "\n".join(f"{k}: {v}" for k, v in request.headers.items())
        body = "" if request.body is None else request.body.decode() if isinstance(request.body, bytes) else request.body
        print(f"{request.method} {request.path_url}\nHeaders:\n{headers}\nBody:\n{body}")


    def add_auth_header(self, headers: Dict[str, str]):
        """
        Modifies headers
        """
        headers["X-Authorization"] = "Bearer " + self.get_token()


    def get_paged(self, params: str, msg: str) -> List[Dict[str, Any]]:
        """ Make requests to get data that might span multiple pages.  Mostly intended for internal use. """
        page_size = 100
        all_data: List[Dict[str, Any]] = []
        page = 0

        if "?" in params:
            joiner = "&"
        else:
            joiner = "?"

        while True:
            resp = self.get(f"{params}{joiner}page={page}&pageSize={page_size}", msg)
            data = resp["data"]
            all_data += data

            if not resp["hasNext"]:
                break

            page += 1

        return all_data


    def get(self, params: str, msg: str) -> Any:            # List[Dict[str, Any]] ??
        if self.mothership_url is None:     # type: ignore
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


    def post(self, params: str, data: Optional[Union[str, Dict[str, Any]]], msg: str) -> Any:
        """
        Data can be a string or a dict
        """
        url = self.mothership_url + params
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.add_auth_header(headers)

        if self.verbose:
            req = requests.Request("POST", url, json=data, headers=headers)
            TbApi.pretty_print_request(req)

        if isinstance(data, str):
            data = Json.loads(data)

        resp = requests.post(url, json=data, headers=headers)
        self.validate_response(resp, msg)

        if not resp.text:
            return {}

        return resp.json()


    @staticmethod
    def validate_response(resp: requests.Response, msg: str) -> None:
        try:
            resp.raise_for_status()
        except requests.exceptions.RequestException as ex:
            ex.args += (msg, f"RESPONSE BODY: {resp.content.decode('utf8')}")       # Append response to the exception to make it easier to diagnose
            raise


class ConfigurationError(Exception):
    pass


class TokenError(Exception):
    pass


U = TypeVar("U", "Customer", "Device", "DeviceProfile", "DeviceProfileInfo")

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
