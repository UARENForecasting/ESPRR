import datetime as dt
import json
import os
from uuid import uuid1


import pymysql
import pytest


@pytest.fixture(scope="session")
def connection():
    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user="root",
        password="testpassword",
        database="esprr_data",
        binary_prefix=True,
    )
    return connection


@pytest.fixture(scope="session")
def auth0_id():
    return "auth0|testuserid"


@pytest.fixture(scope="session")
def user_id():
    return str(uuid1())


@pytest.fixture(scope="session", params=[0, 1])
def bad_user(request):
    if request.param:
        return "auth0|otheruser"
    else:
        return "invalid"


@pytest.fixture(scope="session")
def system_id():
    return str(uuid1())


@pytest.fixture(scope="session")
def system_def():
    return "A System", json.dumps({"version": "1", "other_parameters": []})


@pytest.fixture(scope="session")
def system_hash():
    return "3d5423d4ca558b5c0d820f4280a34f25"


@pytest.fixture(scope="session")
def otherid():
    return str(uuid1())


@pytest.fixture(scope="session")
def standard_test_data(
    auth0_id,
    user_id,
    connection,
    system_id,
    system_def,
    otherid,
):
    curs = connection.cursor()
    curs.executemany(
        "insert into users (id, auth0_id) values (uuid_to_bin(%s, 1), %s)",
        [(user_id, auth0_id), (otherid, "auth0|otheruser")],
    )
    curs.execute(
        "insert into systems (id, user_id, name, definition) values "
        "(uuid_to_bin(%s, 1), uuid_to_bin(%s, 1), %s, %s)",
        (system_id, user_id, *system_def),
    )
    extime = dt.datetime(2020, 1, 3, 12, 34)
    err = "[]"
    curs.executemany(
        "insert into system_data (system_id, dataset, timeseries, statistics, error, created_at, modified_at) "
        "values (uuid_to_bin(%s, 1), %s, %s, %s, %s, %s, %s)",
        [
            (system_id, "prepared", None, None, "{}", extime, extime),
            (system_id, "complete", "timeseries", "stats", err, extime, extime),
            (system_id, "timeseries missing", None, "stats", err, extime, extime),
            (system_id, "statistics missing", "timeseries", None, err, extime, extime),
            (system_id, "error", None, None, '{"message": "fail"}', extime, extime),
        ],
    )
    connection.commit()
    yield
    curs.executemany(
        "delete from users where id = uuid_to_bin(%s, 1)", (user_id, otherid)
    )
    curs.execute("delete from systems where id = uuid_to_bin(%s, 1)", system_id)
    curs.execute(
        "delete from system_data where system_id = uuid_to_bin(%s, 1)", system_id
    )
    connection.commit()


@pytest.fixture()
def cursor(connection, standard_test_data):
    yield connection.cursor()
    connection.rollback()


@pytest.fixture()
def dictcursor(connection, standard_test_data):
    yield connection.cursor(pymysql.cursors.DictCursor)
    connection.rollback()
