from typing import Any
from faker import Faker
import uuid
import requests
from datetime import datetime, timezone

from thingsboard_api_tools.Customer import Customer, CustomerId
from thingsboard_api_tools.TbModel import Id
from tests.helpers import get_tbapi_from_env


fake = Faker()
tbapi = get_tbapi_from_env()


def test_get_all_customers():
    tbapi.get_all_customers()


def test_customer_id():
    """ There's something goofy in the code here; make sure that customer_id passes smoke test. """
    cust = tbapi.get_all_customers()[0]
    cust_id = cust.customer_id
    assert isinstance(cust_id, CustomerId)
    assert cust_id.id == cust.id
    assert cust_id.id.entity_type == "CUSTOMER"


def test_create_edit_and_delete_customer():
    orig_custs = tbapi.get_all_customers()
    name = fake_cust_name()
    attr_val = fake.name()
    key1 = fake.name()
    key2 = fake.name()

    data: dict[str, Any] = {
        "name": name,
        "address": fake.address().split("\n")[0],
        "address2": "",
        "city": fake.city(),
        "state": fake.state(),
        "zip": fake.postcode(),
        "country": "",
        "email": fake.email(),
        "phone": fake.phone_number(),
        "additional_info": {"key1": key1, "key2": key2},
    }

    # Create a customer using this factory method
    cust = tbapi.create_customer(**data, server_attributes={"test_attr": attr_val})     # type: ignore

    assert cust.id.entity_type == "CUSTOMER"

    dumped = cust.model_dump()
    for k, v in data.items():
        assert dumped[k] == v
    assert cust.additional_info and cust.additional_info["key1"] == key1 and cust.additional_info["key2"] == key2

    # Verify the attribute we passed got set
    attr = cust.get_server_attributes()["test_attr"]
    assert attr.key == "test_attr"
    assert attr.value == attr_val

    all_custs = tbapi.get_all_customers()

    assert len(all_custs) == len(orig_custs) + 1
    assert find_id(all_custs, cust.id)

    # Edit
    cust.name = fake_cust_name()
    cust.city = fake.city()
    cust.update()

    cust2 = tbapi.get_customer_by_id(cust.id)
    assert cust2
    assert cust2.name == cust.name
    assert cust2.city == cust.city

    # Delete
    assert cust.delete()

    all_custs = tbapi.get_all_customers()
    assert len(all_custs) == len(orig_custs)
    assert not find_id(all_custs, cust.id)


def test_get_cust_by_bad_name():
    assert tbapi.get_customer_by_name(fake.name()) is None      # Bad name brings back no customers


def test_update_bogus_customer():
    """ Not a likely scenario, mostly curious what happens. """
    cust = tbapi.get_all_customers()[0]
    cust.id.id = str(uuid.uuid4())

    try:
        cust.update()
    except requests.HTTPError:
        pass
    else:
        assert False


def test_created_time():
    # Let's make sure that using a datetime is ok for created_time.  This test is causing problems
    # because server time differs from our time. Hence the ugliness.
    c = tbapi.create_customer(fake_cust_name())
    msg = f"{datetime.now(timezone.utc)}, {c.created_time}"
    assert c.created_time
    assert (datetime.now(timezone.utc) - c.created_time).seconds < 10 or (c.created_time - datetime.now(timezone.utc)).seconds < 10, msg
    assert c.delete()       # Cleanup


def test_get_customer_by_name():
    cust = tbapi.get_all_customers()[-1]
    assert cust.name

    cust2 = tbapi.get_customer_by_name(cust.name)
    assert cust2 and cust2.id == cust.id


def find_id(custs: list[Customer], id: Id):
    for c in custs:
        if c.id.id == id.id:
            return True

    return False


def test_is_public():
    device = tbapi.create_device(name=fake_cust_name(), type=None, label=None)
    assert device.get_customer() is None

    device.make_public()
    assert device.is_public()

    public_customer = device.get_customer()
    assert public_customer
    assert public_customer.name == "Public"         # This really is the public customer
    assert public_customer.is_public()              # <<< This is what we want to test

    not_public_customer = tbapi.get_all_customers()[0]
    assert not_public_customer.name != "Public"     # This isn't the public customer
    assert not not_public_customer.is_public()      # <<< This is what we want to test

    assert device.delete()     # Cleanup


def test_saving():
    old_phone = fake.phone_number()
    cust = tbapi.create_customer(fake_cust_name(), phone=old_phone)
    cust2 = tbapi.get_customer_by_id(cust.id)
    assert cust2
    assert old_phone == cust2.phone

    new_phone = fake.phone_number()
    cust.phone = new_phone               # Change the attribute

    # Verify the attribute hasn't changed on the server
    cust3 = tbapi.get_customer_by_id(cust.id)
    assert cust3
    assert cust3.phone == old_phone
    cust.update()
    cust3 = tbapi.get_customer_by_id(cust.id)
    assert cust3
    assert cust3.phone == new_phone

    assert cust.delete()


def test_get_devices():
    cust = tbapi.create_customer(name=fake_cust_name())

    assert cust.delete()


def fake_cust_name():
    return "__TEST_CUST__ " + fake.name()
