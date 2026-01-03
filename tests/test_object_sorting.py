from typing import Any

from thingsboard_api_tools.TbApi import SortOrder
import tests.helpers as helpers


tbapi = helpers.get_tbapi_from_env()


def test_basic_sorting_multiple_ways():
    """ Testing sorting algorithm itself, not whether it works for different kinds of objects."""

    # Optional list of (field_name, sort_order) tuples, where sort_order is SortOrder.ASC or SortOrder.DESC.
    #     e.g.: [("name", SortOrder.ASC), ("zip", SortOrder.DESCENDING)]
    # Could also be a list of fields (all ascending)
    #     e.g. ["name", "zip"]
    # Even a string will work for simple cases:
    #     e.g. "name" or "zip desc"


    old_get_paged = tbapi.get_paged     # Faster than repeated requests
    tbapi.get_paged = helpers.mock_get_paged_customers.__get__(tbapi)

    unsorted_custs = [(c.name,) for c in tbapi.get_all_customers()]      # No sorting

    custs = [(c.name, ) for c in tbapi.get_all_customers(sort_by="name ASC")]   # Field and sort order
    assert custs == sort(unsorted_custs, 0, reverse=False)

    custs = [(c.name,) for c in tbapi.get_all_customers(sort_by="name")]       # Field only, defaults to ascending
    assert custs == sort(unsorted_custs, 0, reverse=False)

    custs = [(c.name,) for c in tbapi.get_all_customers(sort_by="name descending")]    # Field and sort order, descending
    assert custs == sort(unsorted_custs, 0, reverse=True)

    unsorted_zips = [(c.zip,) for c in tbapi.get_all_customers()]
    zips = [(c.zip,) for c in tbapi.get_all_customers(sort_by=[("zip", SortOrder.ASC)])]
    assert zips == sort(unsorted_zips, 0, reverse=False)

    zips = [(c.zip,) for c in tbapi.get_all_customers(sort_by=[("zip", SortOrder.DESCENDING)])]
    assert zips == sort(unsorted_zips, 0, reverse=True)

    # Some phone numbers are null, and some of those have email addresses that are not null.
    unsorted_mixed = [(c.phone, c.email) for c in tbapi.get_all_customers()]
    mixed = [(c.phone, c.email) for c in tbapi.get_all_customers(sort_by=[("phone", SortOrder.ASC), ("email", SortOrder.DESCENDING)])]

    assert mixed == sort(sort(unsorted_mixed, 1, reverse=True), 0, reverse=False)


    # Different calling syntax
    unsorted_mixed = [(c.phone, c.email) for c in tbapi.get_all_customers()]
    mixed = [(c.phone, c.email) for c in tbapi.get_all_customers(sort_by=["phone", "email"])]

    assert mixed == sort(sort(unsorted_mixed, 1, reverse=False), 0, reverse=False)

    tbapi.get_paged = old_get_paged


def test_id_and_tenant_id_sorting():
    """ Ids and tenant_ids require a special sort mode; try that out here. """

    old_get_paged = tbapi.get_paged     # Faster than repeated requests
    tbapi.get_paged = helpers.mock_get_paged_customers.__get__(tbapi)

    for field in ("id", "tenant_id"):
        unsorted_ids = [(c.__getattribute__(field).id,) for c in tbapi.get_all_customers()]
        ids = [(c.__getattribute__(field).id,) for c in tbapi.get_all_customers(sort_by=[(field, SortOrder.ASC)])]
        assert ids == sort(unsorted_ids, 0, reverse=False)


        unsorted_ids = [(c.__getattribute__(field).id,) for c in tbapi.get_all_customers()]
        ids = [(c.__getattribute__(field).id,) for c in tbapi.get_all_customers(sort_by=[(f"{field} desc")])]
        assert ids == sort(unsorted_ids, 0, reverse=True)


        # Use ids with other items
        unsorted_mixed = [(c.phone, c.__getattribute__(field).id, c.email) for c in tbapi.get_all_customers()]
        mixed = [(c.phone, c.__getattribute__(field).id, c.email) for c in tbapi.get_all_customers(sort_by=[("phone", SortOrder.ASC), (field, SortOrder.ASC), ("email", SortOrder.DESCENDING)])]

        assert mixed == sort(sort(sort(unsorted_mixed, 2, reverse=True), 1, reverse=False), 0, reverse=False)

    # Both together:
    unsorted_mixed = [(c.tenant_id.id, c.id.id) for c in tbapi.get_all_customers()]
    mixed = [(c.tenant_id.id, c.id.id) for c in tbapi.get_all_customers(sort_by=["tenant_id", "id"])]

    assert mixed == sort(sort(unsorted_mixed, 1, reverse=False), 0, reverse=False)

    # Restore order
    tbapi.get_paged = old_get_paged


def test_sorting_with_bad_key():
    """ Ensure that sorting with a non-existent key gives us a rational error. """
    try:
        tbapi.get_all_customers(sort_by=["xxxxx"])
    except AttributeError:
        pass
    else:
        assert False


def test_sorting_device_by_active_status():
    """
    We're essentially testing that boolean sorting works in our modified order, with True before False.
    """
    devices = tbapi.get_all_devices()

    if not any(d.active for d in devices):
        # All devices are inactive; make one active for the test
        devices[0].send_telemetry({"active_test_delete_me": 1})

    devices = tbapi.get_all_devices(sort_by="active")        # Puts active devices first

    active = [d.active for d in devices]
    assert active == sorted(active, reverse=True)    # Python sorts bools with False before True by default, so reverse it


def sort(unsorted: list[tuple[Any | None, ...]], index: int, reverse: bool):
    """ Not easy to use, but only needed here, for testing. """
    return sorted(unsorted, key=lambda x: ((x[index] is None, x[index])), reverse=reverse)
