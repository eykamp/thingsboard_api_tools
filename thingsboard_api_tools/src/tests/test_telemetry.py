from faker import Faker     # type: ignore
from datetime import datetime
import time
import json as Json

from ..models.Device import prepare_ts
from ..TbApi import TbApi

from config import mothership_url, thingsboard_username, thingsboard_password

assert mothership_url
assert thingsboard_username
assert thingsboard_password

tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)

fake = Faker()      # type: ignore


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
                assert latest == {keys[i]: [{"ts": ts1, "value": data[1][i]}] for i in range(len(keys))}, f'{ {keys[i]: [{"ts": ts1, "value": data[1][i]}] for i in range(len(keys))} } should equal {latest} >> Try #{tries}'
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
            assert(
                set([Json.dumps(tel[k][x]) for x in (0, 1)]) ==
                set([Json.dumps({"ts": [ts0, ts1][x], "value": data[x][i]}) for x in (0, 1)])
            )

        # Specify a time range that will only bring back first item we sent
        tel = dev.get_telemetry(keys, start_ts=1000000, end_ts=ts0 + 500)
        for i, k in enumerate(keys):
            assert len(tel[k]) == 1
            assert(tel[k][0] == {"ts": ts0, "value": data[0][i]})

    finally:
        dev.delete()


def test_prepare_timestamp():
    t = datetime.now()
    e = prepare_ts(t)       # Converts datetimes...

    assert e == int(t.timestamp() * 1000)       # Kind of lame... this is just what the fn does
    assert e == prepare_ts(e)   # ...but lets ints through unmolested




def fake_device_name():
    return "__TEST_DEV__ " + fake.name()
