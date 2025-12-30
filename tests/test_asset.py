from tests.helpers import get_tbapi_from_env


tbapi = get_tbapi_from_env()


def test_get_asset_types():
    tbapi.get_asset_types()     # Just make sure it doesn't blow up
