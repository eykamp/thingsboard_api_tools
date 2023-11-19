from faker import Faker     # type: ignore

from ..models.Device import Device
from ..TbApi import TbApi

from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)

fake = Faker()      # type: ignore


def test_get_all_devices():
    tbapi.get_all_devices()


def test_create_device():
    """
    Tests creating a device without specifying a customer
    Also tests  get_device_by_name(name), get_server_attributes(), get_shared_attributes(), device.delete()
    """
    name = fake_device_name() + " " + fake.name()
    server_attributes=fake.pydict(4, allowed_types=(str, int))
    shared_attributes=fake.pydict(4, allowed_types=(str, int))

    device = tbapi.create_device(
        name=name,
        type=fake.company(),
        label=fake.bban(),
        additional_info=fake.pydict(3, allowed_types=(str, int, float)),
        customer=None,
        server_attributes=server_attributes,
        shared_attributes=shared_attributes,
    )

    # Verify we can find the device
    dev = tbapi.get_device_by_name(name)
    assert dev

    assert device.model_dump() == dev.model_dump()
    assert dev.customer_id.id  == TbApi.NULL_GUID                  # No customer specified gets null id

    assert dev.tenant_id == tbapi.get_current_user().tenant_id     # Tenant get assigned to login id's tenant

    # Make sure our attributes got set
    attrs = dev.get_server_attributes()
    assert attrs["active"]      # Should be added by the server
    for k, v in server_attributes.items():
        assert attrs[k].value == v

    attrs = dev.get_shared_attributes()
    for k, v in shared_attributes.items():
        assert attrs[k].value == v

    # Cleanup
    assert device.delete()
    assert tbapi.get_device_by_name(name) is None


def test_create_device_with_customer():
    """
    If you specify a customer when creating a device, make sure that customer gets assigned

    Tests creating a device without specifying a customer
    Also tests  get_device_by_name(name)
    """
    name = fake_device_name() + " " + fake.name()
    server_attributes=fake.pydict(4, allowed_types=(str, int))
    shared_attributes=fake.pydict(4, allowed_types=(str, int))

    customer = tbapi.get_all_customers()[0]

    device = tbapi.create_device(
        name=name,
        type=fake.company(),
        label=fake.bban(),
        additional_info=fake.pydict(3, allowed_types=(str, int, float)),
        customer=customer,
        server_attributes=server_attributes,
        shared_attributes=shared_attributes,
    )

    dev = tbapi.get_device_by_name(name)
    assert dev
    assert dev.customer_id == customer.id

    assert device.delete()


def test_make_public_and_is_public():
    device: Device = tbapi.create_device(name=fake_device_name())
    assert device.get_customer() is None
    assert not device.is_public()

    device.make_public()
    assert device.is_public()

    assert device.delete()     # Cleanup


def test_assign_to():
    device: Device = tbapi.create_device(name=fake_device_name())
    assert device.get_customer() is None

    customer = tbapi.get_all_customers()[0]
    assert customer

    device.assign_to(customer)
    assert device.get_customer() == customer

    dev = tbapi.get_device_by_name(device.name)
    assert dev
    assert dev == device
    assert dev.get_customer() == customer

    assert device.delete()     # Cleanup


def test_double_delete():
    device: Device = tbapi.create_device(name=fake_device_name())
    assert device.delete()          # Device exists: Return True
    assert not device.delete()      # Device doesn't exist: No error, return False


def test_saving():
    old_label = fake.color_name()
    device = tbapi.create_device(fake_device_name(), label=old_label)
    device2 = tbapi.get_device_by_id(device.id)
    assert device2
    assert old_label == device2.label

    new_label = fake.color_name()
    device.label = new_label               # Change the attribute

    # Verify the attribute hasn't changed on the server
    device3 = tbapi.get_device_by_id(device.id)
    assert device3
    assert device3.label == old_label
    device.update()

    device3 = tbapi.get_device_by_id(device.id)
    assert device3
    assert device3.label == new_label

    assert device.delete()


def fake_device_name():
    return "__TEST_DEV__ " + fake.name()
