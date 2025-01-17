from requests import HTTPError
# from faker import Faker     # type: ignore

from thingsboard_api_tools.TbApi import TbApi
from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

# fake = Faker()      # type: ignore

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)

def test_get_all_tenants():
    try:
        tbapi.get_all_tenants()
    except HTTPError as ex:
        assert ex.response.status_code == 403          # If we don't have permissions, we can't test this


def test_get_tenant_assets():
    tbapi.get_tenant_assets()


def test_get_tenant_devices():
    tbapi.get_tenant_devices()


# Don't have the methods for this yet
# def test_saving():
#     old_email = fake.email()
#     tenant = tbapi.create_tenant(fake_cust_name(), email=old_email)
#     tenant2 = tbapi.get_tenant_by_id(tenant.id)
#     assert tenant2
#     assert old_email == tenant2.email

#     new_email = fake.email_number()
#     tenant.email = new_email               # Change the attribute

#     # Verify the attribute hasn't changed on the server
#     tenant3 = tbapi.get_tenant_by_id(tenant.id)
#     assert tenant3
#     assert tenant3.email == old_email
#     tenant.update()
#     tenant3 = tbapi.get_tenant_by_id(tenant.id)
#     assert tenant3
#     assert tenant3.email == new_email

#     assert tenant.delete()