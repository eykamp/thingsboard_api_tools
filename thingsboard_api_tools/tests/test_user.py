from TbApi import TbApi
from models.TbModel import Id
from models.User import User

from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)


def test_get_current_user():
    assert isinstance(tbapi.get_current_user(), User)


def test_get_tenant_id():
    assert isinstance(tbapi.get_current_tenant_id(), Id)
