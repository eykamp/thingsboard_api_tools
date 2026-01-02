from faker import Faker
from datetime import datetime, timedelta
import time
import json as Json

from thingsboard_api_tools.Device import Device, prepare_ts
from thingsboard_api_tools.TelemetryRecord import TelemetryRecord
from tests.helpers import get_tbapi_from_env


fake = Faker()
tbapi = get_tbapi_from_env()


def test_new_device_has_no_telemetry():
    """ Make sure things work as expected when there is no telemetry to be had. """
    dev = tbapi.create_device(fake_device_name())
    try:
        tel = dev.get_telemetry("xxx")

        assert len(tel) == 0
        telkeys = dev.get_telemetry_keys()
        assert len(telkeys) == 0

    finally:
        dev.delete()


def test_telemetry():
    """ Tests send_telemetry(), get_latest_telemetry(), and get_telemetry(). """
    dev = tbapi.create_device(fake_device_name())
    keys = [fake.last_name(), fake.last_name(), fake.last_name()]
    data = [(fake.pystr(), fake.pystr(), fake.pystr()) for _ in range(2)]   # Only test with str to avoid precision and .0 issues

    try:
        # Send a single record
        dev.send_telemetry({keys[i]: data[0][i] for i in range(len(keys))})
        ts0 = 0     # Kill warning

        tries = 20
        while tries > 0:
            try:
                latest = dev.get_latest_telemetry(keys[0])
                ts0 = latest[keys[0]][0]["ts"]      # ts0 is a time assigned by the server, which may be out of sync on machine running tests

                assert latest == {keys[0]: [{"ts": ts0, "value": data[0][0]}]}, f"Try #{tries}"      # Get latest with single key
                latest = dev.get_latest_telemetry([keys[1], keys[2]])
                assert latest == {keys[i]: [{"ts": ts0, "value": data[0][i]}] for i in (1, 2)}, f"Try #{tries}"  # Get latest with multiple keys
            except AssertionError:
                tries -= 1
                if tries == 0:
                    raise
                time.sleep(.25)
            else:
                break


        # Send data with a timestamp, make sure it's later than ts0 so these values will be "latest"; sometimes server clock is out of sync
        ts1 = ts0 + 2500
        dev.send_telemetry({keys[i]: data[1][i] for i in range(len(keys))}, ts=ts1)


        tries = 20
        while tries > 0:
            try:
                latest = dev.get_latest_telemetry(keys)
                assert latest == {keys[i]: [{"ts": ts1, "value": data[1][i]}] for i in range(len(keys))}, f'{{keys[i]: [{"ts": ts1, "value": data[1][i]}] for i in range(len(keys))}} should equal {latest} >> Try #{tries}'
                assert set(dev.get_telemetry_keys()) == set(keys), f"Try #{tries}"   # Use set to make order not matter... because it doesn't

            except AssertionError:
                tries -= 1
                if tries == 0:
                    raise
                time.sleep(.25)
            else:
                break
        # We aren't trying to test end_ts here, but due to time differences on client and server, we
        # need to do this to be sure we get back the data we expect.  Unlikely to be important in
        # production.
        tel = dev.get_telemetry(keys, end_ts=ts1 + 1000)
        for i, k in enumerate(keys):
            # Again, use sets to ensure we don't get tripped up by the order in which the data comes back
            set1 = set([Json.dumps(tel[k][x]) for x in (0, 1)])
            set2 = set([Json.dumps({"ts": [ts0, ts1][x], "value": data[x][i]}) for x in (0, 1)])
            assert set1 == set2

        # Specify a time range that will only bring back first item we sent
        tel = dev.get_telemetry(keys, start_ts=1000000, end_ts=ts0 + 500)
        for i, k in enumerate(keys):
            assert len(tel[k]) == 1
            assert tel[k][0] == {"ts": ts0, "value": data[0][i]}

    finally:
        dev.delete()


def test_get_latest_telemetry_no_data_present():
    """
    Not terribly useful, but I wrote it while working something else out, and it documents this edge case.
    """
    dev: Device = tbapi.create_device(fake_device_name())
    keys = [fake.last_name(), fake.last_name(), fake.last_name()]

    try:
        # First, what happens if we have no telemetry at all?  Should return an emptyish dict.
        # {
        #   'Griffin' = [{'ts': 1767382168999, 'value': None}],
        #   'Moran'   = [{'ts': 1767382168996, 'value': None}],
        #   'Snyder ' = [{'ts': 1767382168995, 'value': None}],
        # }
        data = dev.get_latest_telemetry(keys)
        assert set(keys) == set(data.keys()), "Expected all requested keys to be present"
        assert all(data[k][0]["value"] is None for k in keys), "Expected None values when no telemetry exists"
        assert all(len(data[k]) == 1 for k in keys), "Expected single record per key when no telemetry exists"

    finally:
        dev.delete()


def test_get_latest_telemetry_with_timedelta():
    dev: Device = tbapi.create_device(fake_device_name())
    keys = [fake.last_name(), fake.last_name(), fake.last_name()]
    data = [(fake.pystr(), fake.pystr(), fake.pystr()) for _ in range(20)]   # Only test with str to avoid precision and .0 issues

    try:
        now = datetime.now()
        ins_delta = timedelta(seconds=10)       # Insert points this far apart

        # Insert a series of data rows, each 10 seconds apart, marching back from now() - 10s
        # i.e. most recent data is 10s ago, then 20s ago, etc.
        for i in range(len(data)):
            dev.send_telemetry({keys[j]: data[i][j] for j in range(len(keys))}, ts=now - ins_delta * (i + 1))

        latest = dev.get_latest_telemetry(keys)
        assert latest == {keys[j]: [{"ts": prepare_ts(now - ins_delta), "value": data[0][j]}] for j in range(len(keys))}, "Latest data mismatch"

        # The following tests will also confirm that get_latest_telemetry() with time param returns
        # same data as fully parameterized call to get_telemetry()

        # Most recent data was inserted 10 seconds ago, so getting latest with time=5s should return nothing
        delta = timedelta(seconds=5)
        latest = dev.get_latest_telemetry(keys, time=delta)
        gettel = dev.get_telemetry(keys, start_ts=datetime.now() - delta)
        assert latest == gettel == {}, "Expected no data when time delta is less than time of most recent inserted data"


        # This request should get all data
        points_to_get = len(data)
        delta = timedelta(seconds=100000)
        latest = dev.get_latest_telemetry(keys, time=delta)
        gettel = dev.get_telemetry(keys, start_ts=datetime.now() - delta)

        expected: dict[str, list[dict[str, str | int]]] = {
            keys[j]: [
                {"ts": prepare_ts(now - ins_delta * (i + 1)), "value": data[i][j]} for i in range(points_to_get)
            ] for j in range(len(keys))
        }
        assert latest == gettel == expected, "Expected latest with large time delta to match full telemetry fetch"

        # This request should get some, but not all data
        points_to_get = 5
        start_dt: datetime = now - ins_delta * points_to_get  # dt corresponding to <points_to_get> data points back

        latest = dev.get_latest_telemetry(keys, time=datetime.now() - start_dt)
        gettel = dev.get_telemetry(keys, start_ts=start_dt, end_ts=datetime.now())

        # What we expect to get back
        expected: dict[str, list[dict[str, str | int]]] = {
            keys[j]: [
                {"ts": prepare_ts(now - ins_delta * (i + 1)), "value": data[i][j]} for i in range(points_to_get)
            ] for j in range(len(keys))
        }

        assert latest == gettel == expected, f"Expected to get last {points_to_get} data points"

        # And verify that limit param works as expected (since we have everything all set up)
        limit = 3
        assert limit < points_to_get, "Limit should be less than points_to_get for this test"

        latest = dev.get_latest_telemetry(keys, time=datetime.now() - start_dt, limit=limit)
        gettel = dev.get_telemetry(keys, start_ts=start_dt, end_ts=datetime.now(), limit=limit)

        # What we expect to get back
        expected: dict[str, list[dict[str, str | int]]] = {
            keys[j]: [
                {"ts": prepare_ts(now - ins_delta * (i + 1)), "value": data[i][j]} for i in range(limit)
            ] for j in range(len(keys))
        }

        assert latest == gettel == expected, f"Expected to get last {limit} data points"

    finally:
        dev.delete()


def test_prepare_timestamp():
    t = datetime.now()
    e = prepare_ts(t)       # Converts datetimes...

    assert e == int(t.timestamp() * 1000)       # Kind of lame... this is just what the fn does
    assert e == prepare_ts(e)   # ...but lets ints through unmolested


def test_telemetry_record_serializer():
    """ There was something weird about this serializer... test fixed up version. """
    import re

    ts = datetime.now()
    telrec = TelemetryRecord(values={"a": 1, "b": "two"}, ts=ts)

    assert telrec.ts == ts

    # Test that str(telrec) contains "ts: <epoch_in_ms>" format
    telrec_str = str(telrec)
    assert re.search(r"ts: \d{13}", telrec_str), f"Expected 'ts: <epoch_ms>' pattern in: {telrec_str}"


def fake_device_name():
    """ Returns a fake name with __TEST_DEV__ prefix to make it easy to identify test devices. """
    return "__TEST_DEV__ " + fake.name()
