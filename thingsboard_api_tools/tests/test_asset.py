from TbApi import TbApi

from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)


def test_get_asset_types():
    tbapi.get_asset_types()     # Just make sure it doesn't blow up