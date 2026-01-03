from faker import Faker

from thingsboard_api_tools.TbApi import TbApi
from thingsboard_api_tools.Device import Device
from tests.helpers import get_tbapi_from_env


fake = Faker()
tbapi = get_tbapi_from_env()


def test_get_all_devices():
    tbapi.get_all_devices()


def test_device_sort():
    """ Confirm sorting mechanism has been implemented.  Complete sorting functionality tested in test_object_sorting. """
    lst_1 = tbapi.get_all_devices(sort_by="id asc")
    lst_2 = tbapi.get_all_devices(sort_by="id desc")

    assert lst_1 == list(reversed(lst_2))


def test_create_device():
    """
    Tests creating a device without specifying a customer
    Also tests  get_device_by_name(name), get_server_attributes(), get_shared_attributes(), device.delete()
    """
    name = fake_device_name() + " " + fake.name()
    server_attributes = fake.pydict(4, allowed_types=(str, int))    # type: ignore (pydict)
    shared_attributes = fake.pydict(4, allowed_types=(str, int))    # type: ignore (pydict)

    device = tbapi.create_device(
        name=name,
        type=fake.company(),
        label=fake.bban(),
        additional_info=fake.pydict(3, allowed_types=(str, int, float)),            # type: ignore (pydict)
        customer=None,
        server_attributes=server_attributes,
        shared_attributes=shared_attributes,
    )

    try:

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

    finally:    # Cleanup
        assert device.delete()
        assert tbapi.get_device_by_name(name) is None


def test_create_device_with_customer():
    """
    If you specify a customer when creating a device, make sure that customer gets assigned

    Tests creating a device without specifying a customer
    Also tests  get_device_by_name(name)
    """
    name = fake_device_name() + " " + fake.name()
    server_attributes = fake.pydict(4, allowed_types=(str, int))    # type: ignore (pydict)
    shared_attributes = fake.pydict(4, allowed_types=(str, int))    # type: ignore (pydict)

    customer = tbapi.get_all_customers()[0]

    device = tbapi.create_device(
        name=name,
        type=fake.company(),
        label=fake.bban(),
        additional_info=fake.pydict(3, allowed_types=(str, int, float)),        # type: ignore (pydict)
        customer=customer,
        server_attributes=server_attributes,
        shared_attributes=shared_attributes,
    )

    dev = tbapi.get_device_by_name(name)
    assert dev
    try:
        assert dev.customer_id == customer.id
    finally:
        assert device.delete()


def test_make_public_and_is_public():
    device: Device = tbapi.create_device(name=fake_device_name())
    try:
        assert device.get_customer() is None
        assert not device.is_public()

        device.make_public()
        assert device.is_public()

    finally:
        assert device.delete()     # Cleanup

def test_assign_to():
    device: Device = tbapi.create_device(name=fake_device_name())
    try:
        assert device.get_customer() is None

        customer = tbapi.get_all_customers()[0]
        assert customer

        device.assign_to(customer)
        assert device.get_customer() == customer

        dev = tbapi.get_device_by_name(device.name)
        assert dev

        # Version number will change, so we'll blank that out before comparing:
        assert device.version == 1 and dev.version == 2
        device.version = dev.version = 0
        assert dev == device

        assert dev.get_customer() == customer

    finally:
        assert device.delete()     # Cleanup


def test_filter_by_active():
    """
    Typically, all devices on TB server are inactive.  If you are running tests on a server where
    all devices are active, this test may fail and need to be modified to ensure at least one active
    and one inactive device exist.

    But in most cases this will be fine.
    """
    all_devices = tbapi.get_all_devices()

    if not any(d.active for d in all_devices):
        # Find an inactive device:
        dev = None
        for dev in all_devices:
            if not dev.active:
                break

        assert dev, "If this ever trips we may need to create an inactive device for the test"

        dev.send_telemetry({"active_test_delete_me": 1})  # Insert a bit of telemetry to make device active

        all_devices = tbapi.get_all_devices()
        assert any(d.active for d in all_devices), "Failed to make at least one device active for the test"

    # API counts
    active_devices = tbapi.get_all_devices(is_active=True)
    inactive_devices = tbapi.get_all_devices(is_active=False)

    # Manual counts
    active_count = sum(1 for d in all_devices if d.active)
    inactive_count = sum(1 for d in all_devices if not d.active)

    # Make sure results from the API match manual counts
    assert active_count > 0 and inactive_count > 0, "If this trips, may need to modify test to ensure active and inactive devices"
    assert len(all_devices) > 0 and len(active_devices) > 0 and len(inactive_devices) > 0
    assert len(all_devices) == len(active_devices) + len(inactive_devices)
    assert active_count == len(active_devices)
    assert inactive_count == len(inactive_devices)

    # And ensure we didn't break sorting because we're now handling multiple parameters
    all_devices = tbapi.get_all_devices(is_active=True, sort_by="id asc")


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
