from uuid import uuid1


from pymysql.err import OperationalError
import pytest


def test_system_foreign_key(cursor, system_id):
    cursor.execute(
        "select 1 from system_data where system_id = uuid_to_bin(%s, 1)", system_id
    )
    assert cursor.fetchone()[0]
    cursor.execute("delete from systems where id = uuid_to_bin(%s, 1)", system_id)
    cursor.execute(
        "select 1 from system_data where system_id = uuid_to_bin(%s, 1)", system_id
    )
    assert len(cursor.fetchall()) == 0


def test_create_system_data(cursor, auth0_id, system_id):
    cursor.execute(
        "select 1 from system_data where system_id = uuid_to_bin(%s, 1)"
        ' and dataset = "a"',
        system_id,
    )
    assert len(cursor.fetchall()) == 0
    cursor.execute(f'call create_system_data("{auth0_id}", "{system_id}", "a")')
    cursor.execute(
        "select 1 from system_data where system_id = uuid_to_bin(%s, 1)"
        ' and dataset = "a"',
        system_id,
    )
    assert cursor.fetchone()[0]


def test_create_system_data_bad_id(cursor, auth0_id):
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call create_system_data("{auth0_id}", "{str(uuid1())}", "a")')
    assert err.value.args[0] == 1142


def test_create_system_data_bad_user(cursor, bad_user, system_id):
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call create_system_data("{bad_user}", "{system_id}", "a")')
    assert err.value.args[0] == 1142


@pytest.mark.parametrize("err", ["[]", '{"message": "fail"}'])
def test_update_system_data(auth0_id, dictcursor, system_id, err):
    dictcursor.execute(
        "select * from system_data where system_id = uuid_to_bin(%s, 1) and dataset = %s",
        (system_id, "prepared"),
    )
    before = dictcursor.fetchone()
    for k in ("timeseries", "statistics", "version", "system_hash"):
        assert before[k] is None

    new = {
        "timeseries": b"all the dataz",
        "statistics": b"mean",
        "error": err,
        "version": "v1.0",
        "un_system_hash": "A" * 32,
    }

    dictcursor.execute(
        "call update_system_data(%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            auth0_id,
            system_id,
            "prepared",
            *new.values(),
        ),
    )
    dictcursor.execute(
        "select *, hex(system_hash) as un_system_hash from system_data where system_id = uuid_to_bin(%s, 1) and dataset = %s",
        (system_id, "prepared"),
    )
    after = dictcursor.fetchone()
    for k, v in new.items():
        assert after[k] == v
    assert after["modified_at"] > before["modified_at"]
    assert after["created_at"] == before["created_at"]


def test_update_system_data_bad_dataset(cursor, auth0_id, system_id):
    new = {
        "timeseries": b"all the dataz",
        "statistics": b"mean",
        "error": "[]",
        "version": "v1.0",
        "un_system_hash": "A" * 32,
    }

    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call update_system_data("{auth0_id}", "{system_id}"'
            ', "a", %s, %s, %s, %s, %s)',
            list(new.values()),
        )
    assert err.value.args[0] == 1142


def test_update_system_data_bad_id(cursor, auth0_id):
    new = {
        "timeseries": b"all the dataz",
        "statistics": b"mean",
        "error": "[]",
        "version": "v1.0",
        "un_system_hash": "A" * 32,
    }

    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call update_system_data("{auth0_id}", "{str(uuid1())}"'
            ', "a", %s, %s, %s, %s, %s)',
            list(new.values()),
        )
    assert err.value.args[0] == 1142


def test_update_system_data_bad_user(cursor, bad_user, system_id):
    new = {
        "timeseries": b"all the dataz",
        "statistics": b"mean",
        "error": "[]",
        "version": "v1.0",
        "un_system_hash": "A" * 32,
    }

    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call update_system_data("{bad_user}", "{system_id}",'
            '"a", %s, %s, %s, %s, %s)',
            list(new.values()),
        )
    assert err.value.args[0] == 1142


@pytest.mark.parametrize(
    "dataset,res",
    [
        ("prepared", None),
        ("complete", b"timeseries"),
        ("statistics missing", b"timeseries"),
        ("timeseries missing", None),
        pytest.param(
            "what", None, marks=pytest.mark.xfail(strict=True, raises=AssertionError)
        ),
    ],
)
def test_get_system_timeseries(system_id, dictcursor, dataset, auth0_id, res):
    dictcursor.execute(
        f'call get_system_timeseries("{auth0_id}", "{system_id}", "{dataset}")'
    )
    result = dictcursor.fetchall()
    assert len(result) == 1
    assert result[0]["timeseries"] == res


def test_get_system_timeseries_bad_id(
    otherid,
    cursor,
    auth0_id,
):
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call get_system_timeseries("{auth0_id}", "{otherid}", "a")')
    assert err.value.args[0] == 1142


def test_get_system_timeseries_bad_user(
    system_id,
    bad_user,
    cursor,
):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call get_system_timeseries("{bad_user}", "{system_id}", "prepared")'
        )
    assert err.value.args[0] == 1142


@pytest.mark.parametrize(
    "dataset,res",
    [
        ("prepared", None),
        ("complete", b"stats"),
        ("statistics missing", None),
        ("timeseries missing", b"stats"),
        pytest.param(
            "what", None, marks=pytest.mark.xfail(strict=True, raises=AssertionError)
        ),
    ],
)
def test_get_system_statistics(system_id, dictcursor, dataset, auth0_id, res):
    dictcursor.execute(
        f'call get_system_statistics("{auth0_id}", "{system_id}", "{dataset}")'
    )
    result = dictcursor.fetchall()
    assert len(result) == 1
    assert result[0]["statistics"] == res


def test_get_system_statistics_bad_id(
    otherid,
    cursor,
    auth0_id,
):
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call get_system_statistics("{auth0_id}", "{otherid}", "a")')
    assert err.value.args[0] == 1142


def test_get_system_statistics_bad_user(
    system_id,
    bad_user,
    cursor,
):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call get_system_statistics("{bad_user}", "{system_id}", "prepared")'
        )
    assert err.value.args[0] == 1142


@pytest.mark.parametrize(
    "dataset",
    ["prepared", "complete", "statistics missing", "timeseries missing", "error"],
)
def test_get_system_meta(system_id, dictcursor, dataset, auth0_id):
    dictcursor.execute(
        f'call get_system_data_meta("{auth0_id}", "{system_id}", "{dataset}")'
    )
    res = dictcursor.fetchone()
    assert res["status"] == dataset
    assert res["created_at"] <= res["modified_at"]
    assert res["system_id"] == system_id
    assert res["dataset"] == dataset
    assert res["version"] is None
    assert res["system_hash"] is None


def test_get_system_meta_missing(dictcursor, auth0_id, system_id):
    with pytest.raises(OperationalError) as err:
        dictcursor.execute(
            f'call get_system_data_meta("{auth0_id}", "{system_id}", "nope")'
        )
    assert err.value.args[0] == 1142


def test_get_system_meta_bad_user(cursor, system_id, bad_user):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call get_system_data_meta("{bad_user}", "{system_id}", "prepared")'
        )
    assert err.value.args[0] == 1142


def test_get_system_meta_bad_id(cursor, system_id, auth0_id, otherid):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            f'call get_system_data_meta("{auth0_id}", "{otherid}", "prepared")'
        )
    assert err.value.args[0] == 1142
