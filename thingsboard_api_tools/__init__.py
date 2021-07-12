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
from typing import Dict, Any
from enum import Enum


class EntityType(Enum):
    CUSTOMER = "CUSTOMER"
    DASHBOARD = "DASHBOARD"
    DEVICE = "DEVICE"


# class TbObjectType(Enum):
#     dashboard = Dashboard
#     customer = Customer
#     device = Device


#####################################
# Tests

if __name__ == "__main__":

    from TbApi import TbApi
    from requests.exceptions import HTTPError
    from Device import Device, AttributeScope
    from TbModel import Id

    def get_birdhouses(tbapi: TbApi):
        return tbapi.get_devices_by_name("Birdhouse")


    def compare_dicts(d1: Dict[str, Any], d2: Dict[str, Any], path: str = ""):
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
    try:
        from config import mothership_url, thingsboard_username, thingsboard_password
    except:
        mothership_url = None
        thingsboard_username = None
        thingsboard_password = None



    print("Loading data...", end=None)
    assert mothership_url and thingsboard_username and thingsboard_password

    tbapi = TbApi(mothership_url, thingsboard_username, thingsboard_password)

    def get_test_device() -> Device:
        device = tbapi.get_device_by_name("Birdhouse 001")
        assert device
        return device


    device = get_test_device()  # redundant (repeated below)
    customer = tbapi.get_customer_by_name("Birdhouse 001")  # redundant (repeated below)
    dash = tbapi.get_dashboard_by_name("Birdhouse 001 Dash")
    dash_def = tbapi.get_dashboard_by_id("0d538a70-d996-11e7-a394-bf47d8c29be7")

    assert customer
    assert dash

    # Validate the EntityType enum
    assert device.id.entity_type == EntityType.DEVICE.value
    assert customer.id.entity_type == EntityType.CUSTOMER.value
    assert dash.id.entity_type == EntityType.DASHBOARD.value
    assert dash_def.id.entity_type == EntityType.DASHBOARD.value


    # try:
    #     bogus = tbapi.get_dashboard_definition("3d538a70-d996-11e7-a394-bf47d8c29be7")   # Bogus guid
    #     assert False
    # except HTTPError:
    #     pass

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
    token = device.token
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

    assert device.get_customer().id == customer.id and customer.id == device.get_customer().id
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

    device.set_server_attributes({"delme": "123"})
    found = False
    keys = device.get_server_attributes()
    for key in keys:
        if key["key"] == "delme":
            found = True
    assert found
    device.delete_server_attributes("delme")
    found = False
    keys = device.get_server_attributes()
    for key in keys:
        if key["key"] == "delme":
            found = True
    assert not found

    print(" done with first round of tests.")

    print("testing devices round 2")

    exit()





    # # create a new device
    # shared_attributes = {"my_shared_attribute_1": 111}
    # server_attributes = {"my_server_attribute_2": 222}
    # device = tbapi.add_device("Device Test Subject", "Guinea Pig", shared_attributes=shared_attributes, server_attributes=server_attributes)

    # assert(isinstance(device.get_customer(), Customer)) # should be a guid
    # token = device.token
    # assert(isinstance(token, str))
    # assert(len(token) == 20)

    # # Customer tests
    # print("now testing customers")

    # customer = tbapi.get_customer_by_name("Birdhouse 001")

    # assert isinstance(customer, Customer)
    # assert isinstance(customer.id, Id)
    # assert tbapi.get_customer_by_id(customer.id.id) == customer
    # assert tbapi.get_customer_by_id(customer.id) == customer

    # assert tbapi.get_customer_by_name("Does Not Exist") is None

    # customers = tbapi.get_customers_by_name("Birdhouse 0")
    # assert len(customers) > 1
    # assert isinstance(customers[0], Customer)

    # customers = tbapi.get_customers_by_name("Does Not Exist")
    # assert len(customers) == 0

    # customers = tbapi.get_all_customers()
    # assert len(customers) > 1
    # assert isinstance(customers[0], Customer)


    # try:
    #     print(customer.additionalInfo)     # Should not be accessible -- we remapped this name
    #     assert False
    # except AttributeError:
    #     pass

    # # Assign an unknown attribute -- should raise exception
    # try:
    #     customer.unknown = "LLL"
    #     assert False
    # except ValueError:
    #     pass

    # # Assign an unknown attribute II -- should raise exception
    # try:
    #     customer["unknown"] = "LLL"
    #     assert False
    # except TypeError:
    #     pass

    # # Access an unknown attribute -- should raise exception
    # try:
    #     print(customer.unknown)
    #     assert False
    # except AttributeError:
    #     pass

    # # Access an unknown attribute II -- should raise exception
    # try:
    #     print(customer["strange"])
    #     assert False
    # except TypeError:
    #     pass


    # # Construct with an unknown attribute -- should raise exception
    # bad_cust_dict = customer.dict(by_alias=True)
    # bad_cust_dict["unknown_attr"] = 666
    # try:
    #     bad_c = Customer.from_dict(bad_cust_dict)
    #     assert False
    # except AttributeError:
    #     pass

    # # Time handled correctly (also verifies name translation: createdTime -> created_time -> createdTime)
    # assert(isinstance(customer.created_time, datetime))            # Rehydrated time is a datetime
    # assert(isinstance(json.loads(customer.json(by_alias=True))["createdTime"], int))     # Serialized time is int



    # # Dashboard built right?
    # assert type(dash.assigned_customers[0]) is CustomerId

    # # Check attribute renaming at top level -- incoming json uses createdTime, we remap to created_time.  Make sure it works.
    # assert dash.created_time
    # try:
    #     dash.createdTime
    #     assert False
    # except AttributeError:
    #     pass

    # # And check remapping when converting back to json
    # assert json.loads(dash.json(by_alias=True)).get("createdTime")
    # assert json.loads(dash.json(by_alias=True)).get("created_time") is None

    # # Check nested attribute renaming
    # assert dash.assigned_customers[0].customer_id.entity_type == EntityType.CUSTOMER.value
    # try:
    #     dash.assigned_customers[0].customer_id.entityType
    #     assert False
    # except AttributeError:
    #     pass
    # assert json.loads(dash.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entityType") == EntityType.CUSTOMER.value
    # assert json.loads(dash.json(by_alias=True))["assignedCustomers"][0].get("customerId", {}).get("entity_type") is None

    # # assert(Device.from_dict(d.to_dict).to_dict == d.to_dict)


    # # Serialized looks like original?
    # # compare_dicts(dev_json, json.loads(d.json(by_alias=True)))


    # # Check GuidList[Id, Customer] ==> should fail

    # assert dash.is_public() is True



    # # Device telemetry tests -- TODO: make sure these clean up after themselves!
    # keys = ["datum_1", "datum_2"]
    # values = [555, 666]
    # timestamps = [1595897301 * 1000, 1595897302 * 1000] # second timestamp must be greater than first for check to work


    # expected_tel_keys = []
    # tel_keys = device.get_telemetry_keys()
    # assert(tel_keys == expected_tel_keys)


    # expected_telemetry = {}
    # expected_latest_telemetry = {}


    # def test_sending_telemetry(device: Device, data_index: int, timestamp_index: int):
    #     device.send_telemetry({keys[data_index]: values[data_index]}, timestamp=timestamps[timestamp_index])
    #     if keys[data_index] not in expected_tel_keys:
    #         expected_tel_keys.append(keys[data_index])
    #     tel_keys = device.get_telemetry_keys()
    #     assert(tel_keys == expected_tel_keys)

    #     if keys[data_index] not in expected_telemetry.keys():
    #         expected_telemetry[keys[data_index]]  = [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    #     else:
    #         expected_telemetry[keys[data_index]].insert(0, {"ts": timestamps[timestamp_index], "value": str(values[data_index])})
    #         # expected_telemetry[keys[data_index]] += [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    #     telemetry = device.get_telemetry(tel_keys)
    #     assert(telemetry == expected_telemetry)

    #     expected_latest_telemetry[keys[data_index]] = [{"ts": timestamps[timestamp_index], "value": str(values[data_index])}]
    #     latest_telemetry = device.get_latest_telemetry(tel_keys)
    #     assert(latest_telemetry == expected_latest_telemetry)


    # test_sending_telemetry(device, 0, 0)
    # test_sending_telemetry(device, 1, 0)
    # test_sending_telemetry(device, 0, 1)


    # # for tel_key in tel_keys:
    # #     for timestamp in timestamps:
    # #         device.delete_telemetry(tel_key, timestamp)
    # # telemetry = device.get_telemetry(tel_keys)
    # # assert(telemetry == {})



    # def check_attributes(device_attributes: List[Dict[str, Any]], expected_attributes: Dict[str, Any], expected=True):
    #     # device_attributes is a list of dicts, formatted [{"key": key, "lastUpdateTs": int, "value": val}]
    #     for expected_key, expected_val in expected_attributes.items():
    #         match: bool = False
    #         for attr in device_attributes: # a dict, formatted [{"key": key, "lastUpdateTs": int, "value": val}]
    #             if attr["key"] == expected_key and attr["value"] == expected_val:   # not checking the timestamps
    #                 match = True
    #         assert(match == expected)


    # new_attributes = {"my_new_attribute_3": 333, "my_new_attribute_4": 444}
    # expected_attributes_for_shared_scope = {**shared_attributes, **new_attributes}

    # expected_attributes_for_server_scope = {**server_attributes, **new_attributes}

    # device.set_shared_attributes(new_attributes)
    # device.set_server_attributes(new_attributes)
    # check_attributes(device.get_shared_attributes(), expected_attributes_for_shared_scope, True)
    # check_attributes(device.get_server_attributes(), expected_attributes_for_server_scope, True)
    # device.delete_shared_attributes([*(expected_attributes_for_shared_scope.keys())])
    # device.delete_server_attributes([*(expected_attributes_for_server_scope.keys())])
    # check_attributes(device.get_shared_attributes(), expected_attributes_for_shared_scope, False)
    # check_attributes(device.get_server_attributes(), expected_attributes_for_server_scope, False)


    # device.set_attributes({**shared_attributes, **new_attributes}, AttributeScope.SHARED)
    # device.set_attributes({**server_attributes, **new_attributes}, AttributeScope.SERVER)
    # check_attributes(device.get_attributes(AttributeScope.SHARED), expected_attributes_for_shared_scope, True)
    # check_attributes(device.get_attributes(AttributeScope.SERVER), expected_attributes_for_server_scope, True)
    # device.delete_attributes([*(expected_attributes_for_shared_scope.keys())], AttributeScope.SHARED)
    # device.delete_attributes([*(expected_attributes_for_server_scope.keys())], AttributeScope.SERVER)
    # check_attributes(device.get_attributes(AttributeScope.SHARED), expected_attributes_for_shared_scope, False)
    # check_attributes(device.get_attributes(AttributeScope.SERVER), expected_attributes_for_server_scope, False)


    # device = device.assign_to_public_user()
    # assert(device.is_public())

    # assert device.delete()
    # assert not device.delete()      # Can't delete again

    # try:
    #     test_sending_telemetry(device, token, 1, 1)
    # except requests.exceptions.HTTPError:
    #     print("the device has been successfully deleted!")


    # print("done testing devices round 2")
