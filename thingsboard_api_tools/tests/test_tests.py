from typing import Dict, Any

import os
import sys


# import TbModel

# from TbModel import Id, Attributes, TbObject
from TbApi import TbApi, NULL_GUID
# from models.TbModel import Id, Attributes, TbObject
# from models.Customer import Customer, CustomerId
# from models.Dashboard import Dashboard, DashboardDef
# from models.Device import Device, AggregationType
# from models.DeviceProfile import DeviceProfile, DeviceProfileInfo


from requests.exceptions import HTTPError
from datetime import datetime
import json
import uuid


# Get the secret stuff
# try:
#     from config import mothership_url, thingsboard_username, thingsboard_password
# except:
#     mothership_url = None
#     thingsboard_username = None
#     thingsboard_password = None


def test_config():
    """ We need these to do anything. """
    from config import mothership_url, thingsboard_username, thingsboard_password

    assert mothership_url
    assert thingsboard_username
    assert thingsboard_password


# def compare_dicts(d1: Dict[str, Any], d2: Dict[str, Any], path: str = ""):
#     for k in d1:
#         if (k not in d2):
#             print(path, ":")
#             print(k + " as key not in d2", "\n")
#         else:
#             if type(d1[k]) is dict:
#                 if path == "":
#                     path = k
#                 else:
#                     path = path + "->" + k
#                 compare_dicts(d1[k], d2[k], path)
#             else:
#                 if d1[k] != d2[k]:
#                     print(path, ":")
#                     print(" - ", k, " : ", d1[k])
#                     print(" + ", k, " : ", d2[k])






# print("Loading data...", end=None)
# assert mothership_url and thingsboard_username and thingsboard_password

# tbapi = TbApi(mothership_url, thingsboard_username, thingsboard_password)

# all_devices = tbapi.get_all_devices()
# assert len(all_devices) > 0

# # Find a valid device name
# device_name = None
# device_id = None
# for device in all_devices:
#     # Get a device that has a name and has been assigned to a non-public customer
#     if device.name and device.customer_id.id != NULL_GUID and tbapi.get_public_user_id() != device.customer_id:
#         device_name = device.name
#         device_id = device.id
#         break
# if not device_name and device_id:
#     raise Exception("Could not find a device with both a name and non-public customer in the database")

# dev_1 = tbapi.get_device_by_name(device_name)
# dev_2 = tbapi.get_device_by_id(device_id)

# assert dev_1 == dev_2

# dev_prof_1 = dev_1.get_profile()
# dev_prof_2 = tbapi.get_device_profile_by_id(dev_1.device_profile_id)

# assert dev_prof_1 == dev_prof_2

# dev_prof_info_1 = dev_1.get_profile_info()
# dev_prof_info_2 = tbapi.get_device_profile_info_by_id(dev_1.device_profile_id)

# assert dev_prof_info_1 == dev_prof_info_2



# all_device_profiles = tbapi.get_all_device_profiles()
# assert len(all_device_profiles) > 0

# # Find a valid device_profile name
# device_profile_name = None
# for device_profile in all_device_profiles:
#     # Get a device_profile that has a name and has been assigned to a non-public customer
#     if device_profile.name:
#         device_profile_name = device_profile.name
#         device_profile_id = device_profile.id
#         break
# if not device_profile_name:
#     raise Exception("Could not find a device_profile with a non-empty name in the database")


# dev_prof_1 = tbapi.get_device_profile_by_name(device_profile_name)
# dev_prof_2 = tbapi.get_device_profile_by_id(device_profile_id)

# assert dev_prof_1 == dev_prof_2


# all_device_profile_infos = tbapi.get_all_device_profile_infos()
# assert len(all_device_profile_infos) > 0

# # Find a valid device_profile_info name
# device_profile_info_name = None
# for device_profile_info in all_device_profile_infos:
#     # Get a device_profile_info that has a name and has been assigned to a non-public customer
#     if device_profile_info.name:
#         device_profile_info_name = device_profile_info.name
#         device_profile_info_id = device_profile_info.id
#         break
# if not device_profile_info_name:
#     raise Exception("Could not find a device_profile_info with a non-empty name in the database")


# dev_prof_inf_1 = tbapi.get_device_profile_info_by_name(device_profile_info_name)
# dev_prof_inf_2 = tbapi.get_device_profile_info_by_id(device_profile_info_id)

# assert dev_prof_inf_1 == dev_prof_inf_2





# all_customers = tbapi.get_all_customers()
# assert len(all_customers) > 0

# customer_name = None
# for customer in all_customers:
#     if customer.name and customer.name != "Public":
#         customer_name = customer.name
#         break
# if not customer_name:
#     raise Exception("Could not find a customer with a name in the database")


# all_dashboards = tbapi.get_all_dashboards()
# assert len(all_dashboards) > 0

# dashboard_name = None
# for dashboard in all_dashboards:
#     if dashboard.name:
#         dashboard_name = dashboard.name
#         dashboard_id = dashboard.id
#         break
# if not dashboard_name:
#     raise Exception("Could not find a dashboard with a name in the database")

# # Get things by name
# device = tbapi.get_device_by_name(device_name)
# assert device
# assert isinstance(device, Device)
# assert isinstance(device.id, Id)
# assert device.id.entity_type == EntityType.DEVICE.value
# assert tbapi.get_device_by_name("Does Not Exist") is None      # Bogus name -> failure returns None

# customer = tbapi.get_customer_by_name(customer_name)
# assert customer
# assert isinstance(customer, Customer)
# assert isinstance(customer.id, Id)
# assert customer.id.entity_type == EntityType.CUSTOMER.value
# assert tbapi.get_customer_by_name("Does Not Exist") is None    # Bogus name -> failure returns None

# dashboard = tbapi.get_dashboard_by_name(dashboard_name)
# assert dashboard
# assert isinstance(dashboard, Dashboard)
# assert isinstance(dashboard.id, Id)
# assert dashboard.id.entity_type == EntityType.DASHBOARD.value
# assert tbapi.get_dashboard_by_name("Does Not Exist") is None   # Bogus name -> failure returns None

# token = device.token
# assert isinstance(token, str)
# assert len(token) == 20     # Tokens are always 20 character strings




# # TODO: Put elsewhere
# # Create a new device, customer, and dashboard
# device_name = "test_device_" + uuid.uuid4().hex
# new_device = tbapi.create_device(device_name, "testtype", "mylabel", customer, additional_info={"key": "val"})
# new_device2 = tbapi.get_device_by_name(device_name)
# # Is the entity we got back from create the same as we get from get?
# assert new_device2 and new_device.dict() == new_device2.dict()
# assert new_device2.customer_id == customer.id       # Setting up customer id takes a special step... verify we got it right

# assert new_device.additional_info is not None
# new_device.additional_info["thing2"] = 1234         # Add additional additional_info
# new_device2 = tbapi.get_device_by_name(device_name)
# assert new_device2 and new_device.dict() != new_device2.dict()      # Not yet written to database
# new_device.update()
# new_device2 = tbapi.get_device_by_name(device_name)
# assert new_device2 and new_device.dict() == new_device2.dict()      # Not yet written to database



# assert device.delete()
# assert not device.delete()      # Can't delete again



# T = Type[TbObject]

# # Get things using ids, both valid and invlaid
# def test_get_by_id(cls: T, get_function: Callable[[str], List[T]], id: str):
#     assert isinstance(get_function(id.id), cls)     # Retrieve a device by its guid
#     assert isinstance(get_function(id), cls)        # Retrieve a device by an Id object
#     try:
#         get_function("3d538a70-d996-11e7-a394-bf47d8c29be7")      # Bogus guid -> failure raises exception
#         assert False
#     except HTTPError:
#         pass

# test_get_by_id(Device, tbapi.get_device_by_id, device.id)
# test_get_by_id(Customer, tbapi.get_customer_by_id, customer.id)
# test_get_by_id(Dashboard, tbapi.get_dashboard_by_id, dashboard.id)
# test_get_by_id(DeviceProfile, tbapi.get_device_profile_by_id, device_profile.id)
# test_get_by_id(DeviceProfileInfo, tbapi.get_device_profile_info_by_id, device_profile_info.id)




# # Retrieve things with a partial name and with a bogus name
# def test_get_by_name(cls: T, get_function: Callable[[str], List[T]], name: str):
#     items = get_function(name[:int(len(name) / 2) + 1])
#     assert len(items) >= 1
#     assert isinstance(items[0], cls)
#     items = get_function("Does Not Exist")      # Will return nothing
#     assert len(items) == 0

# test_get_by_name(Device, tbapi.get_devices_by_name, device_name)
# test_get_by_name(Customer, tbapi.get_customers_by_name, customer_name)
# test_get_by_name(Dashboard, tbapi.get_dashboards_by_name, dashboard_name)
# test_get_by_name(DeviceProfile, tbapi.get_device_profiles_by_name, device_profile_name)
# test_get_by_name(DeviceProfileInfo, tbapi.get_device_profile_infos_by_name, device_profile_info_name)



# # Set/retrieve/delete attributes
# def test_attributes(entity: Union[Device, Customer], scope: Attributes.Scope):
#     key = "test_delete_me_" + uuid.uuid4().hex      # This will be unique on each run
#     val = 12345

#     # Verify key doesn't exist
#     attrs = tbapi.get_attributes(entity, scope)
#     assert key not in attrs         # If this assert fails, either delete the attribute key from the server, or choose a different key

#     # Set
#     tbapi.set_attributes(entity, {key: val}, scope)
#     attrs = tbapi.get_attributes(entity, scope)

#     assert key in attrs and attrs[key].value == val

#     # Cleanup
#     entity.delete_attributes(key, scope)
#     attrs = tbapi.get_attributes(entity, scope)
#     assert key not in attrs

#     ### Do same thing, but with named methods:

#     entity.set_shared_attributes({key: val}) if scope == Attributes.Scope.SHARED else entity.set_server_attributes({key: val})
#     attrs = entity.get_shared_attributes() if scope == Attributes.Scope.SHARED else entity.get_server_attributes()

#     assert key in attrs and attrs[key].value == val

#     # Cleanup
#     entity.delete_shared_attributes(key) if scope == Attributes.Scope.SHARED else entity.delete_server_attributes(key)

#     attrs = entity.get_shared_attributes() if scope == Attributes.Scope.SHARED else entity.get_server_attributes()
#     assert key not in attrs


# test_attributes(device, Attributes.Scope.SERVER)
# test_attributes(device, Attributes.Scope.SHARED)
# test_attributes(customer, Attributes.Scope.SERVER)
# test_attributes(customer, Attributes.Scope.SHARED)
# # test_attributes(dashboard, Attributes.Scope.SERVER)       # Doesn't appear to be implemented by the server
# # test_attributes(dashboard, Attributes.Scope.SHARED)       # Doesn't appear to be implemented by the server
# test_attributes(device_profile, Attributes.Scope.SERVER)
# test_attributes(device_profile, Attributes.Scope.SHARED)
# test_attributes(device_profile_info, Attributes.Scope.SERVER)
# test_attributes(device_profile_info, Attributes.Scope.SHARED)
# # test_attributes(device, Attributes.Scope.CLIENT)    # Client scope does not work on the server



# # Device ownership, public/private
# device.assign_to(customer)      # Not public if assigned to a customer
# assert not device.is_public()
# device = tbapi.get_device_by_id(device.id)  # Get it again to make sure changes stuck
# assert not device.is_public()
# cust = device.get_customer()
# assert cust and cust.id == customer.id and customer.id == cust.id

# device.make_public()
# assert device.is_public()                   # Locally marked as public?
# device = tbapi.get_device_by_id(device.id)  # Get it again to make sure changes were made on the server
# assert device.is_public()

# cust = device.get_customer()
# assert device.get_customer() != customer
# device.assign_to(customer)
# device = tbapi.get_device_by_id(device.id)  # Get it again to make sure changes stuck
# assert device.get_customer() == customer

# # Basic telemetry tests (sending, getting, deleting, etc.)
# before = datetime.now()
# assert isinstance(device.get_telemetry_keys(), list)    # List might be empty if there's no telemetry

# key = "testkey_" + uuid.uuid4().hex                     # Create unique key
# assert key not in device.get_telemetry_keys()
# device.send_telemetry({key: 101})
# assert key in device.get_telemetry_keys()

# device.send_telemetry({key: 102}, ts=1000)              # Give specific timestamp
# assert len(device.get_telemetry(key)[key]) == 2         # Brings back all telemetry for device, which is 2 items

# # Make sure date filtering works
# tel =  device.get_telemetry(key, start_ts=before)[key]  # Using ts filter should only bring back first item; pass datetime object
# assert len(tel) == 1 and tel[0]["value"] == 101
# tel = device.get_telemetry(key, end_ts=2000)[key]       # Using ts filter should only bring back second item; pass epoch time
# assert len(tel) == 1 and tel[0]["value"] == 102

# tel =  device.get_telemetry(key, agg=AggregationType.AVG, interval=10000000000000)[key]   # Need ridiculous interval because spread in telemetry timestamps is so large
# assert len(tel) == 1 and tel[0]["value"] == 101.5

# device.delete_all_telemetry(key)                        # Cleanup
# assert key not in device.get_telemetry_keys()           # All telemetry deleted
# assert device.get_telemetry(key) == {}                  # All telemetry deleted

# # device.delete_all_telemetry(device.get_telemetry_keys())  --> Blows away all telemetry for the device


# # Dashboard ownership, and public/private; similar to but subtly different from Devices.  Dashes can have mutliple owners, Devices only one.
# dashboard.assign_to(customer)
# if dashboard.is_public():
#     was_public = True
#     dashboard.make_private()
# else:
#     was_public = False

# assert not dashboard.is_public()
# dash = tbapi.get_dashboard_by_name(dashboard_name)
# assert dash and dash.assigned_customers is not None
# assert dashboard.assigned_customers is not None
# # We manipulate dashboard while assigning customers... make sure that manipulation gives us the same result we'd have getting a fresh copy
# for cust_id in dash.assigned_customers:
#     assert cust_id in dashboard.assigned_customers
# assert len(dashboard.assigned_customers) == len(dash.assigned_customers)

# dashboard = tbapi.get_dashboard_by_id(dashboard.id)     # Get it again to make sure changes stuck
# assert not dashboard.is_public()
# assert customer.id and dashboard.assigned_customers and customer.id in dashboard.assigned_customers

# dashboard.make_public()
# assert dashboard.is_public()                            # Locally marked as public?
# dashboard = tbapi.get_dashboard_by_id(dashboard.id)     # Get it again to make sure changes were made on the server
# assert dashboard.is_public()

# dashboard.make_private()
# assert not dashboard.is_public()                        # Locally marked as public?
# dashboard = tbapi.get_dashboard_by_id(dashboard.id)     # Get it again to make sure changes were made on the server
# assert not dashboard.is_public()

# if was_public:                                          # Restore things to their earlier state because we're nice
#     dashboard.make_public()




# # A couple of other random things...

# # Time handled correctly (mostly a pydantic configuration thing)
# assert isinstance(customer.created_time, datetime)                                  # Rehydrated time is a datetime
# assert customer.created_time.tzinfo.zone == TIMEZONE.zone       # type: ignore      # and has the expected timezone
# assert isinstance(json.loads(customer.json(by_alias=True))["createdTime"], int)     # Serialized time is int


# # Dashboard built right?
# assert dashboard.assigned_customers
# assert isinstance(dashboard.assigned_customers[0], CustomerId)


# # And check remapping when converting back to json
# assert json.loads(dashboard.json(by_alias=True)).get("createdTime")
# assert json.loads(dashboard.json(by_alias=True)).get("created_time") is None

# assert dashboard.assigned_customers[0].id.entity_type == EntityType.CUSTOMER.value      # TODO: Need to make sure we have a customer (or delete; marginal value)

# assert json.loads(dashboard.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entityType") == EntityType.CUSTOMER.value
# assert json.loads(dashboard.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entity_type") is None

# # def create_device(self, name: str, device_type: Optional[str] = None, label: Optional[str] = None, customer: Optional[Customer] = None, additional_info: Optional[Dict[str, Any]] = None, shared_attributes: Optional[Dict[str, Any]] = None, server_attributes: Optional[Dict[str, Any]] = None) -> "Device":

