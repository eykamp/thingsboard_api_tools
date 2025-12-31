from tests.helpers import get_tbapi_from_env


tbapi = get_tbapi_from_env()


def test_get_all_device_profile_infos():
    tbapi.get_all_device_profile_infos()


def test_device_profile_info_sort():
    """ Confirm sorting mechanism has been implemented.  Complete sorting functionality tested in test_object_sorting. """
    lst_1 = tbapi.get_all_device_profile_infos(sort_by="id asc")
    lst_2 = tbapi.get_all_device_profile_infos(sort_by="id desc")

    assert lst_1 == list(reversed(lst_2))


def test_get_device_profile_info_by_id():
    profile_info = tbapi.get_all_device_profile_infos()[0]
    prof = tbapi.get_device_profile_info_by_id(profile_info.id.id)

    assert prof == profile_info


def test_get_device_profile_info_by_name():
    profile_info = tbapi.get_all_device_profile_infos()[0]
    prof = tbapi.get_device_profile_info_by_name(profile_info.name)

    assert prof == profile_info
