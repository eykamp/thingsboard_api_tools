from typing import Any
from faker import Faker
from requests import HTTPError
from datetime import datetime, timezone
from tests.helpers import get_tbapi_from_env


fake = Faker()
tbapi = get_tbapi_from_env()


def test_server_attributes():
    """ This will work the same for any model inheriting from HasAttributes; no need to test them all. """

    attr_names = ["testattr", "testattr2", "new_test_attr"]
    attr_dict: dict[str, Any] = {attr_names[0]: fake.pyint(), attr_names[1]: fake.pystr()}

    cust = tbapi.create_customer(name=fake_cust_name(), server_attributes=attr_dict)

    try:
        attrs = cust.get_server_attributes()
        assert attr_names[0] in attrs

        atr1_last_updated = attrs[attr_names[0]].last_updated
        assert attrs[attr_names[0]].key == attr_names[0]
        assert attrs[attr_names[0]].value == attr_dict[attr_names[0]]
        assert attrs[attr_names[1]].key == attr_names[1]
        assert attrs[attr_names[1]].value == attr_dict[attr_names[1]]

        # Update by changing attr struct:
        new_attr_val = fake.pybool()     # Also changing type
        attrs[attr_names[0]].value = new_attr_val
        cust.set_server_attributes(attrs)

        attrs2 = cust.get_server_attributes()
        # Server clock is off; this might help
        assert (datetime.now(timezone.utc) - attrs2[attr_names[0]].last_updated).seconds < 10 or (attrs2[attr_names[0]].last_updated - datetime.now(timezone.utc)).seconds < 10
        assert attrs2[attr_names[0]].last_updated > atr1_last_updated       # Time got updated

        # Update by sending dict
        new_attr_val2 = fake.pyint()    # Changing type
        cust.set_server_attributes({attr_names[1]: new_attr_val2})

        attrs3 = cust.get_server_attributes()
        assert (datetime.now(timezone.utc) - attrs3[attr_names[1]].last_updated).seconds < 10 or (attrs3[attr_names[1]].last_updated - datetime.now(timezone.utc)).seconds < 10
        assert attrs3[attr_names[1]].last_updated > atr1_last_updated       # Time got updated

        # Delete an attribute
        assert cust.delete_server_attributes(attr_names[0])
        attrs4 = cust.get_server_attributes()
        assert attr_names[0] not in attrs4 and attr_names[1] in attrs4

        # Delete missing attribute; always returns true if operation generally worked, even if attribute
        # isn't actually present
        assert cust.delete_server_attributes("Kalamazoo!")

        # Add new attribute
        new_val = fake.pystr()
        cust.set_server_attributes({attr_names[2]: new_val})
        attrs4 = cust.get_server_attributes()
        assert attr_names[2] in attrs4 and attr_names[0] not in attrs4 and attr_names[1] in attrs4      # We have the attrs we expect
        assert attrs4[attr_names[2]].last_updated > attrs4[attr_names[1]].last_updated                  # Update times are sane
        assert attrs4[attr_names[2]].value == new_val

        # Ensure no crossover between scopes:
        assert cust.get_client_attributes() == {}       # These make no sense in the customer context, but still work
        assert cust.get_shared_attributes() == {}       # These make no sense in the customer context, but still work

    finally:
        assert cust.delete()

    # Gettting attributes of deleted client fails as expected
    try:
        cust.get_server_attributes()
    except HTTPError as ex:
        assert ex.response.status_code == 404
    else:
        assert False


def fake_cust_name():
    return "__TEST_CUST__ " + fake.name()
