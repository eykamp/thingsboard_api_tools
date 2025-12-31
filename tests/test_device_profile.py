from tests.helpers import get_tbapi_from_env


tbapi = get_tbapi_from_env()


def test_get_all_devices_profiles():
    tbapi.get_all_device_profiles()


def test_device_profile_sort():
    """ Confirm sorting mechanism has been implemented.  Complete sorting functionality tested in test_object_sorting. """
    lst_1 = tbapi.get_all_device_profiles(sort_by="id asc")
    lst_2 = tbapi.get_all_device_profiles(sort_by="id desc")

    assert lst_1 == list(reversed(lst_2))


def test_get_profile_from_device():
    dev = tbapi.get_all_devices()[0]
    assert dev
    assert dev.get_profile()
    assert dev.get_profile_info()


def test_get_device_profile_by_id():
    profile = tbapi.get_all_device_profiles()[0]
    prof = tbapi.get_device_profile_by_id(profile.id.id)

    assert prof == profile


def test_get_device_profile_by_name():
    profile = tbapi.get_all_device_profiles()[0]
    prof = tbapi.get_device_profile_by_name(profile.name)

    assert prof == profile
