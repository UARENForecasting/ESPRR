from base64 import b64decode
from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import tarfile
import tempfile
from uuid import UUID


from fakeredis import FakeRedis  # type: ignore
from fastapi.testclient import TestClient
import httpx
import pandas as pd
import pymysql
import pytest
from rq import Queue  # type: ignore


from esprr_api.data import nsrdb
from esprr_api.main import app
from esprr_api import settings, models, storage, queuing


@pytest.fixture(scope="session")
def auth_token():
    token_req = httpx.post(
        settings.auth_token_url,
        headers={"content-type": "application/json"},
        data=(
            '{"grant_type": "password", '
            '"username": "testing@esprr.x.energy.arizona.edu", '
            '"password": "Thepassword123!", '
            f'"audience": "{settings.auth_audience}", '
            f'"client_id": "{settings.auth_client_id}"'
            "}"
        ),
    )
    if token_req.status_code != 200:  # pragma: no cover
        pytest.skip("Cannot retrieve valid Auth0 token")
    else:
        token = token_req.json()["access_token"]
        return token


@pytest.fixture(scope="module")
def client(auth_token):
    out = TestClient(app)
    out.headers.update({"Authorization": f"Bearer {auth_token}"})
    return out


@pytest.fixture(scope="module")
def noauthclient():
    return TestClient(app)


@pytest.fixture(scope="module")
def root_conn():
    conn = storage._make_sql_connection_partial(user="root", password="testpassword")()
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def add_example_db_data(root_conn):
    curs = root_conn.cursor()
    curs.callproc("add_example_data")
    root_conn.commit()
    yield curs
    curs.callproc("remove_example_data")
    root_conn.commit()


@pytest.fixture()
def nocommit_transaction(mocker):
    conn = storage.engine.connect()

    @contextmanager
    def start_transaction(cls):
        cls._cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        yield cls
        cls._cursor = None

    mocker.patch.object(
        storage.StorageInterface, "start_transaction", new=start_transaction
    )
    yield
    conn.rollback()


@pytest.fixture()
def mock_redis(mocker):
    faker = FakeRedis()
    mocker.patch.object(queuing, "_get_redis_conn", return_value=faker)
    return faker


@pytest.fixture()
def async_queue(mock_redis, mocker):
    q = Queue("jobs", connection=mock_redis)
    mocker.patch.object(queuing, "_get_queue", return_value=q)
    return q


@pytest.fixture(scope="module")
def auth0_id():
    return "auth0|6061d0dfc96e2800685cb001"


@pytest.fixture(scope="module")
def user_id():
    return UUID("17fbf1c6-34bd-11eb-af43-f4939feddd82")


@pytest.fixture(scope="module")
def system_id():
    return models.SYSTEM_ID


@pytest.fixture(scope="module")
def other_system_id():
    return "6513485a-34cd-11eb-8f13-f4939feddd82"


@pytest.fixture()
def system_def():
    return models.PVSystem(**models.SYSTEM_EXAMPLE)


@pytest.fixture()
def stored_system(system_def, system_id):
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    return models.StoredPVSystem(
        object_id=system_id,
        object_type="system",
        created_at=extime,
        modified_at=extime,
        definition=system_def,
    )


@pytest.fixture()
def group_id():
    return "3e622aaa-a187-11ec-ad64-54bf64606445"


@pytest.fixture()
def group_name():
    return "A System Group"


@pytest.fixture()
def stored_system_group(group_id, group_name, stored_system):
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    return models.StoredSystemGroup(
        object_id=group_id,
        object_type="system_group",
        definition={"name": group_name, "systems": [stored_system]},
        created_at=extime,
        modified_at=extime,
    )


@pytest.fixture(scope="session")
def nsrdb_data(pytestconfig):
    tar_path = Path(pytestconfig.rootdir) / "esprr_api/data/nsrdb.zarr.tar"
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        tar = tarfile.open(tar_path, "r")
        tar.extractall(out_path)
        yield out_path / "nsrdb.zarr"


@pytest.fixture()
def dataset(nsrdb_data):
    return nsrdb.NSRDBDataset(nsrdb_data)


@pytest.fixture()
def ready_dataset(dataset):
    dataset.load_grid()
    return dataset


@pytest.fixture()
def dataset_name():
    return "NSRDB_2019"


@pytest.fixture()
def timeseries_df():
    return pd.DataFrame(
        {
            "time": [
                pd.Timestamp("2019-01-01T00:00Z"),
                pd.Timestamp("2019-02-01T00:00Z"),
            ],
            "ac_power": [10.2, 8.2],
            "dc_power": [10.2, 8.2],
            "clearsky_ac_power": [10.2, 8.2],
            "clearsky_dc_power": [10.2, 8.2],
        }
    )


@pytest.fixture()
def timeseries_csv():
    return """time,ac_power,dc_power,clearsky_ac_power,clearsky_dc_power
2018-12-31 17:00:00-07:00,10.2,10.2,10.2,10.2
2019-01-31 17:00:00-07:00,8.2,8.2,8.2,8.2
"""


@pytest.fixture()
def statistics_df():
    return pd.DataFrame(
        {"index": ["Jan.", "Feb."], "10-min": [0.3, 1.2], "sunrise/set": [2.8, 2.2]}
    )


@pytest.fixture()
def statistics_csv():
    return """index,10-min,sunrise/set
Jan.,0.3,2.8
Feb.,1.2,2.2
"""


@pytest.fixture()
def timeseries_bytes():
    return b64decode(
        "QVJST1cxAAD/////GAUAABAAAAAAAAoADgAGAAUACAAKAAAAAAEEABAAAAAAAAoADAAAAAQACAAKAAAAtAMAAAQAAAABAAAADAAAAAgADAAEAAgACAAAAAgAAAAQAAAABgAAAHBhbmRhcwAAfwMAAHsiaW5kZXhfY29sdW1ucyI6IFtdLCAiY29sdW1uX2luZGV4ZXMiOiBbeyJuYW1lIjogbnVsbCwgImZpZWxkX25hbWUiOiBudWxsLCAicGFuZGFzX3R5cGUiOiAidW5pY29kZSIsICJudW1weV90eXBlIjogIm9iamVjdCIsICJtZXRhZGF0YSI6IHsiZW5jb2RpbmciOiAiVVRGLTgifX1dLCAiY29sdW1ucyI6IFt7Im5hbWUiOiAidGltZSIsICJmaWVsZF9uYW1lIjogInRpbWUiLCAicGFuZGFzX3R5cGUiOiAiZGF0ZXRpbWV0eiIsICJudW1weV90eXBlIjogImRhdGV0aW1lNjRbbnNdIiwgIm1ldGFkYXRhIjogeyJ0aW1lem9uZSI6ICJVVEMifX0sIHsibmFtZSI6ICJhY19wb3dlciIsICJmaWVsZF9uYW1lIjogImFjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDY0IiwgIm1ldGFkYXRhIjogbnVsbH0sIHsibmFtZSI6ICJkY19wb3dlciIsICJmaWVsZF9uYW1lIjogImRjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDY0IiwgIm1ldGFkYXRhIjogbnVsbH0sIHsibmFtZSI6ICJjbGVhcnNreV9hY19wb3dlciIsICJmaWVsZF9uYW1lIjogImNsZWFyc2t5X2FjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDY0IiwgIm1ldGFkYXRhIjogbnVsbH0sIHsibmFtZSI6ICJjbGVhcnNreV9kY19wb3dlciIsICJmaWVsZF9uYW1lIjogImNsZWFyc2t5X2RjX3Bvd2VyIiwgInBhbmRhc190eXBlIjogImZsb2F0MzIiLCAibnVtcHlfdHlwZSI6ICJmbG9hdDY0IiwgIm1ldGFkYXRhIjogbnVsbH1dLCAiY3JlYXRvciI6IHsibGlicmFyeSI6ICJweWFycm93IiwgInZlcnNpb24iOiAiNC4wLjEifSwgInBhbmRhc192ZXJzaW9uIjogIjEuMy4wIn0ABQAAAPgAAACwAAAAfAAAAEAAAAAEAAAALP///wAAAQMQAAAAJAAAAAQAAAAAAAAAEQAAAGNsZWFyc2t5X2RjX3Bvd2VyAAAAav///wAAAQBk////AAABAxAAAAAkAAAABAAAAAAAAAARAAAAY2xlYXJza3lfYWNfcG93ZXIAAACi////AAABAJz///8AAAEDEAAAABwAAAAEAAAAAAAAAAgAAABkY19wb3dlcgAAAADS////AAABAMz///8AAAEDEAAAACAAAAAEAAAAAAAAAAgAAABhY19wb3dlcgAABgAIAAYABgAAAAAAAQAQABQACAAGAAcADAAAABAAEAAAAAAAAQoQAAAAIAAAAAQAAAAAAAAABAAAAHRpbWUAAAAACAAIAAAABAAIAAAABAAAAAMAAABVVEMA/////0gBAAAUAAAAAAAAAAwAFgAGAAUACAAMAAwAAAAAAwQAGAAAADAAAAAAAAAAAAAKABgADAAEAAgACgAAALwAAAAQAAAAAgAAAAAAAAAAAAAACgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAABAAAAAAAAAACAAAAAAAAAAYAAAAAAAAAAAAAAAAAAAAGAAAAAAAAAAIAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAgAAAAAAAAAKAAAAAAAAAAAAAAAAAAAACgAAAAAAAAACAAAAAAAAAAAAAAABQAAAAIAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAgK0qXAAAAAAAjFNcAAAAADMzI0EzMwNBMzMjQTMzA0EzMyNBMzMDQTMzI0EzMwNB/////wAAAAAQAAAADAAUAAYACAAMABAADAAAAAAABABAAAAAKAAAAAQAAAABAAAAKAUAAAAAAABQAQAAAAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAKAAwAAAAEAAgACgAAALQDAAAEAAAAAQAAAAwAAAAIAAwABAAIAAgAAAAIAAAAEAAAAAYAAABwYW5kYXMAAH8DAAB7ImluZGV4X2NvbHVtbnMiOiBbXSwgImNvbHVtbl9pbmRleGVzIjogW3sibmFtZSI6IG51bGwsICJmaWVsZF9uYW1lIjogbnVsbCwgInBhbmRhc190eXBlIjogInVuaWNvZGUiLCAibnVtcHlfdHlwZSI6ICJvYmplY3QiLCAibWV0YWRhdGEiOiB7ImVuY29kaW5nIjogIlVURi04In19XSwgImNvbHVtbnMiOiBbeyJuYW1lIjogInRpbWUiLCAiZmllbGRfbmFtZSI6ICJ0aW1lIiwgInBhbmRhc190eXBlIjogImRhdGV0aW1ldHoiLCAibnVtcHlfdHlwZSI6ICJkYXRldGltZTY0W25zXSIsICJtZXRhZGF0YSI6IHsidGltZXpvbmUiOiAiVVRDIn19LCB7Im5hbWUiOiAiYWNfcG93ZXIiLCAiZmllbGRfbmFtZSI6ICJhY19wb3dlciIsICJwYW5kYXNfdHlwZSI6ICJmbG9hdDMyIiwgIm51bXB5X3R5cGUiOiAiZmxvYXQ2NCIsICJtZXRhZGF0YSI6IG51bGx9LCB7Im5hbWUiOiAiZGNfcG93ZXIiLCAiZmllbGRfbmFtZSI6ICJkY19wb3dlciIsICJwYW5kYXNfdHlwZSI6ICJmbG9hdDMyIiwgIm51bXB5X3R5cGUiOiAiZmxvYXQ2NCIsICJtZXRhZGF0YSI6IG51bGx9LCB7Im5hbWUiOiAiY2xlYXJza3lfYWNfcG93ZXIiLCAiZmllbGRfbmFtZSI6ICJjbGVhcnNreV9hY19wb3dlciIsICJwYW5kYXNfdHlwZSI6ICJmbG9hdDMyIiwgIm51bXB5X3R5cGUiOiAiZmxvYXQ2NCIsICJtZXRhZGF0YSI6IG51bGx9LCB7Im5hbWUiOiAiY2xlYXJza3lfZGNfcG93ZXIiLCAiZmllbGRfbmFtZSI6ICJjbGVhcnNreV9kY19wb3dlciIsICJwYW5kYXNfdHlwZSI6ICJmbG9hdDMyIiwgIm51bXB5X3R5cGUiOiAiZmxvYXQ2NCIsICJtZXRhZGF0YSI6IG51bGx9XSwgImNyZWF0b3IiOiB7ImxpYnJhcnkiOiAicHlhcnJvdyIsICJ2ZXJzaW9uIjogIjQuMC4xIn0sICJwYW5kYXNfdmVyc2lvbiI6ICIxLjMuMCJ9AAUAAAD4AAAAsAAAAHwAAABAAAAABAAAACz///8AAAEDEAAAACQAAAAEAAAAAAAAABEAAABjbGVhcnNreV9kY19wb3dlcgAAAGr///8AAAEAZP///wAAAQMQAAAAJAAAAAQAAAAAAAAAEQAAAGNsZWFyc2t5X2FjX3Bvd2VyAAAAov///wAAAQCc////AAABAxAAAAAcAAAABAAAAAAAAAAIAAAAZGNfcG93ZXIAAAAA0v///wAAAQDM////AAABAxAAAAAgAAAABAAAAAAAAAAIAAAAYWNfcG93ZXIAAAYACAAGAAYAAAAAAAEAEAAUAAgABgAHAAwAAAAQABAAAAAAAAEKEAAAACAAAAAEAAAAAAAAAAQAAAB0aW1lAAAAAAgACAAAAAQACAAAAAQAAAADAAAAVVRDAEgFAABBUlJPVzE="  # NOQA
    )


@pytest.fixture()
def statistics_bytes():
    return b64decode(
        "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"  # NOQA
    )
