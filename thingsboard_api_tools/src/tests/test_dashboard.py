from faker import Faker     # type: ignore

from ..TbApi import TbApi
from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password


fake = Faker()

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)


def test_get_all_dashboards():
    tbapi.get_all_dashboards()


def test_get_dashboard_by_id():
    dashboard = tbapi.get_all_dashboards()[0]
    dash = tbapi.get_dashboard_by_id(dashboard.id.id)

    assert dash == dashboard


def test_get_dashboard_by_name():
    dashboard = tbapi.get_all_dashboards()[0]
    assert dashboard

    dash = tbapi.get_dashboard_by_name(dashboard.name)
    assert dash == dashboard


def test_copy_dashboard():
    # We'll probably never build a dasboard from scratch (they're very complicated and very
    # undocumented), so let's grab a dashboard def from somewhere to start with
    dashboard = tbapi.get_all_dashboards()[0]
    template = dashboard.get_definition()

    name = fake_dash_name()
    dash = tbapi.create_dashboard(name, template)

    j1 = dash.model_dump()
    j2 = template.model_dump()

    # New dashboard we just created should be the same as the source dashboard, except for a few fields
    del j1["id"], j2["id"], j1["name"], j2["name"]

    assert j1 == j2

    assert tbapi.get_dashboard_by_name(name)
    dash.delete()
    assert not tbapi.get_dashboard_by_name(name)


def test_saving():
    dash = tbapi.create_dashboard(fake_dash_name())

    try:
        old_order = dash.mobile_order
        new_order = (old_order or 0) + 1       # Protect against None
        dash.mobile_order = new_order               # Change the attribute

        # Verify the attribute hasn't changed on the server
        dash2 = tbapi.get_dashboard_by_id(dash.id)
        assert dash2.mobile_order == old_order
        dash.update()
        dash2 = tbapi.get_dashboard_by_id(dash.id)
        assert dash2.mobile_order == new_order

    finally:
        assert dash.delete()


def test_is_public():
    """ Also tests make_public() and make_private() """
    dash = tbapi.create_dashboard(fake_dash_name())

    assert not dash.is_public()     # Not public by default
    dash.make_public()
    assert dash.is_public()
    dash.make_private()
    assert not dash.is_public()
    assert dash.delete()


def test_assign_to():
    """ Also tests get_customers() """
    dash = tbapi.create_dashboard(fake_dash_name())
    assert dash.get_customers() == []           # No customers by default

    custs = tbapi.get_all_customers()
    assert len(custs) > 0                       # Make sure we have one
    dash.assign_to(custs[0])                    # Assign

    assert dash.get_customers() == [custs[0]]   # We've assigned our customer!

    assert dash.delete()                        # Cleanup


def test_get_public_url():
    """ Also tests make_public() and make_private() """
    dash = tbapi.create_dashboard(fake_dash_name())
    assert dash.get_public_url() is None
    dash.make_public()
    assert dash.get_public_url() and dash.get_public_url().startswith("http")       # type: ignore
    dash.make_private()
    assert dash.get_public_url() is None
    assert dash.delete()


def test_get_config_for_dashboard():
    dash = tbapi.get_all_dashboards()[0]
    dash_def = dash.get_definition()        # Get the full dashboard, including its configuration

    # A dash_def is just a Dashboard with a configuration object
    dict1 = dash.model_dump()
    dict2 = dash_def.model_dump()
    del dict2["configuration"]
    assert dict1 == dict2


def test_dashboard_with_no_widgets():
    dash = tbapi.create_dashboard(fake_dash_name())
    assert dash.configuration is None       # Dashboards with no widgets have no configuration

    dash_def = dash.get_definition()
    assert dash_def.configuration is None

    assert dash.delete()



def fake_dash_name():
    return "__TEST_DASH__ " + fake.name()