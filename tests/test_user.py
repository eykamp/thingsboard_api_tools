from thingsboard_api_tools.TbModel import Id
from thingsboard_api_tools.User import User
from tests.helpers import get_tbapi_from_env


tbapi = get_tbapi_from_env()


def test_get_current_user():
    assert isinstance(tbapi.get_current_user(), User)


def test_get_tenant_id():
    assert isinstance(tbapi.get_current_tenant_id(), Id)
