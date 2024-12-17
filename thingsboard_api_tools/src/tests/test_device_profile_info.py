from src.TbApi import TbApi
from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)


def test_get_all_device_profile_infos():
    tbapi.get_all_device_profile_infos()


def test_get_device_profile_info_by_id():
    profile_info = tbapi.get_all_device_profile_infos()[0]
    prof = tbapi.get_device_profile_info_by_id(profile_info.id.id)

    assert prof == profile_info


def test_get_device_profile_info_by_name():
    profile_info = tbapi.get_all_device_profile_infos()[0]
    prof = tbapi.get_device_profile_info_by_name(profile_info.name)

    assert prof == profile_info
