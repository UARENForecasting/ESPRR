from copy import deepcopy
import datetime as dt
import json
import uuid


from fastapi import HTTPException
import pandas as pd
import pymysql
import pytest


from esprr_api import storage, models, __version__


pytestmark = pytest.mark.usefixtures("add_example_db_data")


@pytest.fixture(scope="module")
def storage_interface(auth0_id):
    out = storage.StorageInterface()
    out.commit = False
    out.user = auth0_id
    return out


def test_escape_timestamp():
    assert (
        storage.escape_timestamp(pd.Timestamp("2019-04-08T030423"))
        == "'2019-04-08 03:04:23'"
    )
    assert (
        storage.escape_timestamp(pd.Timestamp("2019-04-08T030423Z"))
        == "'2019-04-08 03:04:23'"
    )
    assert (
        storage.escape_timestamp(pd.Timestamp("2019-04-08T030423-0300"))
        == "'2019-04-08 06:04:23'"
    )


def test_escape_datetime():
    assert (
        storage.escape_datetime(dt.datetime(2019, 5, 1, 23, 33, 12))
        == "'2019-05-01 23:33:12'"
    )
    assert (
        storage.escape_datetime(
            dt.datetime(
                2019, 5, 1, 23, 33, 12, tzinfo=dt.timezone(dt.timedelta(hours=-5))
            )
        )
        == "'2019-05-02 04:33:12'"
    )


def test_convert_datetime_utc():
    assert storage.convert_datetime_utc("2019-05-01 23:01:32") == dt.datetime(
        2019, 5, 1, 23, 1, 32, tzinfo=dt.timezone(dt.timedelta(hours=0))
    )


def test_no_cursor(storage_interface):
    with pytest.raises(AttributeError):
        storage_interface.cursor


@pytest.mark.parametrize("err", [pymysql.err.OperationalError, HTTPException])
def test_start_transaction_rollback(mocker, err):
    si = storage.StorageInterface()
    conn = mocker.MagicMock()
    mocker.patch.object(storage.engine, "connect", return_value=conn)

    with pytest.raises(err):
        with si.start_transaction():
            raise err(400)
    conn.rollback.assert_called()
    conn.commit.assert_not_called()


def test_start_transaction_commit(mocker):
    si = storage.StorageInterface()
    conn = mocker.MagicMock()
    mocker.patch.object(storage.engine, "connect", return_value=conn)
    with si.start_transaction() as st:
        st.cursor.execute("select 1")
    conn.commit.assert_called()


def test_start_transaction_no_commit(mocker):
    si = storage.StorageInterface()
    si.commit = False
    conn = mocker.MagicMock()
    mocker.patch.object(storage.engine, "connect", return_value=conn)
    with si.start_transaction() as st:
        st.cursor.execute("select 1")
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


@pytest.mark.parametrize(
    "errno,outerr,status_code",
    [
        (1142, HTTPException, 404),
        (1062, HTTPException, 409),
        (3140, HTTPException, 400),
        (1406, HTTPException, 400),
        (1048, HTTPException, 400),
        (1408, pymysql.err.OperationalError, None),
    ],
)
def test_try_query_raises(storage_interface, errno, outerr, status_code):
    with pytest.raises(outerr) as err:
        with storage_interface.start_transaction() as st:
            st.try_query(
                "signal sqlstate '45000' set message_text='',"
                f" mysql_errno = {errno}",
                None,
            )
    if status_code:
        err.value.status_code == status_code


def test_timezone(storage_interface):
    with storage_interface.start_transaction() as st:
        st.cursor.execute("SELECT @@session.time_zone as tz")
        res = st.cursor.fetchone()["tz"]
    assert res == "+00:00"


def test_call_procedure(storage_interface, mocker, auth0_id):
    tryq = mocker.patch.object(storage_interface, "try_query")
    with storage_interface.start_transaction() as st:
        st._cursor = mocker.MagicMock()
        st._call_procedure("the_procedure", 0, "a")
    tryq.assert_called_with("CALL the_procedure(%s,%s,%s)", (auth0_id, 0, "a"))


def test_call_procedure_without_user(storage_interface, mocker):
    tryq = mocker.patch.object(storage_interface, "try_query")
    with storage_interface.start_transaction() as st:
        st._cursor = mocker.MagicMock()
        st._call_procedure("the_procedure", 0, "a", with_current_user=False)
    tryq.assert_called_with("CALL the_procedure(%s,%s)", (0, "a"))


def test_call_procedure_for_single(storage_interface, mocker):
    callp = mocker.patch.object(storage_interface, "_call_procedure", return_value=[0])
    with storage_interface.start_transaction() as st:
        out = st._call_procedure_for_single("the_procedure", 0, "a")
    callp.assert_called()
    assert out == 0


def test_call_procedure_for_single_nothing(storage_interface, mocker):
    mocker.patch.object(storage_interface, "_call_procedure", return_value=[])
    with pytest.raises(HTTPException):
        with storage_interface.start_transaction() as st:
            st._call_procedure_for_single("the_procedure", 0, "a")


def test_delete_system(storage_interface, system_id):
    with storage_interface.start_transaction() as st:
        st.delete_system(system_id)
        assert len(st.list_systems()) == 0


def test_delete_system_dne(
    storage_interface,
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.delete_system(uuid.uuid1())
    assert err.value.status_code == 404


def test_delete_system_wrong_owner(storage_interface, other_system_id):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.delete_system(other_system_id)
    assert err.value.status_code == 404


def test_create_system(storage_interface, system_def):
    system_def.name = "New System"
    with storage_interface.start_transaction() as st:
        sysid = st.create_system(system_def)
        out = st.get_system(sysid.object_id)
    assert out.definition == system_def


def test_create_system_duplicate(storage_interface, system_def):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.create_system(system_def)
    assert err.value.status_code == 409


def test_list_system(storage_interface, stored_system):
    with storage_interface.start_transaction() as st:
        out = st.list_systems()
    assert out == [stored_system]


def test_get_system(storage_interface, stored_system, system_id):
    with storage_interface.start_transaction() as st:
        out = st.get_system(system_id)
    assert out == stored_system


def test_get_system_dne(
    storage_interface,
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system(uuid.uuid1())
    assert err.value.status_code == 404


def test_get_system_wrong_owner(storage_interface, other_system_id):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system(other_system_id)
    assert err.value.status_code == 404


def test_update_system(
    storage_interface,
    stored_system,
    system_id,
    system_def,
    nocommit_transaction,
):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc, microsecond=0)
    system_def.ac_capacity = 9.9
    with storage_interface.start_transaction() as st:
        st.update_system(system_id, system_def)
        out = st.get_system(system_id)
    assert out.definition == system_def
    assert out.created_at == stored_system.created_at
    assert out.modified_at >= now


def test_update_system_duplicate_name(storage_interface, system_def, system_id):
    new_system = deepcopy(system_def)
    new_system.name = "a new name"
    with storage_interface.start_transaction() as st:
        new_id = st.create_system(new_system).object_id
        with pytest.raises(HTTPException) as err:
            st.update_system(new_id, system_def)
    assert err.value.status_code == 409


def test_update_system_dne(storage_interface, system_def):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.update_system(uuid.uuid1(), system_def)
    assert err.value.status_code == 404


def test_update_system_wrong_owner(storage_interface, other_system_id, system_def):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.update_system(other_system_id, system_def)
    assert err.value.status_code == 404


def test_create_user_if_not_exists(storage_interface, mocker):
    now = dt.datetime.utcnow().replace(microsecond=0, tzinfo=dt.timezone.utc)
    mocker.patch.object(storage_interface, "user", new="newuser")
    with storage_interface.start_transaction() as st:
        st.create_user_if_not_exists()
        out = st._call_procedure_for_single("get_user")
    assert out["created_at"] >= now
    assert out["auth0_id"] == "newuser"


def test_create_user_if_not_exists_does_already(storage_interface, auth0_id):
    with storage_interface.start_transaction() as st:
        st.create_user_if_not_exists()
        out = st._call_procedure_for_single("get_user")
    assert out["created_at"] == dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    assert out["auth0_id"] == auth0_id


def test_get_user(storage_interface, auth0_id, user_id):
    with storage_interface.start_transaction() as st:
        out = st.get_user()
    assert out.created_at == dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    assert out.auth0_id == auth0_id
    assert out.object_id == user_id
    assert out.object_type == "user"
    assert out.modified_at == out.created_at


@pytest.fixture()
def cleanup_user(root_conn):
    try:
        yield
    finally:
        curs = root_conn.cursor()
        curs.execute("delete from users where auth0_id = 'newuser'")
        root_conn.commit()


def test_get_user_new(storage_interface, mocker, cleanup_user):
    now = dt.datetime.utcnow().replace(microsecond=0, tzinfo=dt.timezone.utc)
    mocker.patch.object(storage_interface, "user", new="newuser")
    create = mocker.spy(storage_interface, "create_user_if_not_exists")
    with storage_interface.start_transaction() as st:
        out = st.get_user()
    assert out.created_at >= now
    assert out.auth0_id == "newuser"
    assert out.object_type == "user"
    create.assert_called()


def test_get_system_hash(storage_interface, system_id):
    with storage_interface.start_transaction() as st:
        out = st.get_system_hash(system_id)
    assert out == "29b4855d70dc37601bb31323f9703cf1"


def test_get_system_hash_wrong_owner(storage_interface, other_system_id):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_hash(other_system_id)
    assert err.value.status_code == 404


def test_get_system_hash_dne(
    storage_interface,
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_hash(str(uuid.uuid1()))
    assert err.value.status_code == 404


def test_create_system_model_data(
    storage_interface, system_id, system_def, dataset_name
):
    with storage_interface.start_transaction() as st:
        st.delete_system(system_id)
        sysid = st.create_system(system_def).object_id
        with pytest.raises(HTTPException):
            st.get_system_model_meta(sysid, dataset_name)
        st.create_system_model_data(sysid, dataset_name)
        out = st.get_system_model_meta(sysid, dataset_name)
    assert out.status == "queued"
    assert out.dataset == dataset_name
    assert out.system_id == sysid
    assert out.version is None
    assert not out.system_modified


def test_create_system_model_data_existing(storage_interface, system_id, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.create_system_model_data(system_id, dataset_name)
    assert err.value.status_code == 409


def test_create_system_model_data_dne(storage_interface, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.create_system_model_data(str(uuid.uuid1()), dataset_name)
    assert err.value.status_code == 404


def test_create_system_model_data_wrong_owner(
    storage_interface, other_system_id, dataset_name
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.create_system_model_data(other_system_id, dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_meta(storage_interface, system_id, dataset_name):
    with storage_interface.start_transaction() as st:
        out = st.get_system_model_meta(system_id, dataset_name)
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    exp = models.SystemDataMeta(
        system_id=system_id,
        dataset=dataset_name,
        version="v0.1",
        system_modified=False,
        status="complete",
        created_at=extime,
        modified_at=extime,
    )
    assert out == exp


def test_get_system_model_meta_empty(storage_interface, system_id):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_meta(system_id, "NSRDB 2018")
    assert err.value.status_code == 404


def test_get_system_model_meta_wrong_owner(
    storage_interface, other_system_id, dataset_name
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_meta(other_system_id, dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_meta_dne(storage_interface, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_meta(str(uuid.uuid1()), dataset_name)
    assert err.value.status_code == 404


def test_update_system_model_data(
    storage_interface,
    dataset_name,
    system_id,
    timeseries_bytes,
    statistics_bytes,
):
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    before = models.SystemDataMeta(
        system_id=system_id,
        dataset=dataset_name,
        version="v0.1",
        system_modified=False,
        status="complete",
        created_at=extime,
        modified_at=extime,
    )
    with storage_interface.start_transaction() as st:
        assert (
            st.get_system_model_timeseries(system_id, dataset_name) == timeseries_bytes
        )
        assert (
            st.get_system_model_statistics(system_id, dataset_name) == statistics_bytes
        )
        assert st.get_system_model_meta(system_id, dataset_name) == before
        st.update_system_model_data(
            system_id, dataset_name, "a" * 32, b"new timeseries", b"new stats"
        )
        assert (
            st.get_system_model_timeseries(system_id, dataset_name) == b"new timeseries"
        )
        assert st.get_system_model_statistics(system_id, dataset_name) == b"new stats"
        after = st.get_system_model_meta(system_id, dataset_name)
    assert after.modified_at > extime
    assert after.system_modified
    assert after.status == "complete"
    assert after.created_at == extime
    assert after.version == __version__


def test_update_system_model_data_error(
    storage_interface,
    dataset_name,
    system_id,
):
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    with storage_interface.start_transaction() as st:
        st.update_system_model_data(
            system_id,
            dataset_name,
            "a" * 32,
            b"somethighn",
            None,
            [{"message": "failed"}],
        )
        after = st.get_system_model_meta(system_id, dataset_name)
    assert after.modified_at > extime
    assert after.system_modified
    assert after.status == "error"
    assert after.created_at == extime
    assert after.version == __version__


def test_update_system_model_data_bad_types(storage_interface, system_id):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.update_system_model_data(
                system_id, "no exist", "a" * 32, b"new timeseries", b"new stats"
            )
    assert err.value.status_code == 404


def test_update_system_model_data_dne(storage_interface, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.update_system_model_data(
                uuid.uuid1(), dataset_name, "a" * 32, b"new timeseries", b"new stats"
            )
    assert err.value.status_code == 404


def test_update_system_model_data_wrong_owner(
    storage_interface, dataset_name, other_system_id
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.update_system_model_data(
                other_system_id, dataset_name, "a" * 32, b"new timeseries", b"new stats"
            )
    assert err.value.status_code == 404


def test_get_system_model_timeseries(
    storage_interface, system_id, dataset_name, timeseries_bytes
):
    with storage_interface.start_transaction() as st:
        out = st.get_system_model_timeseries(system_id, dataset_name)
    assert out == timeseries_bytes


def test_get_system_model_timeseries_dne(storage_interface, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_timeseries(str(uuid.uuid1()), dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_timeseries_wrong_owner(
    storage_interface, dataset_name, other_system_id
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_timeseries(other_system_id, dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_statistics(
    storage_interface, system_id, dataset_name, statistics_bytes
):
    with storage_interface.start_transaction() as st:
        out = st.get_system_model_statistics(system_id, dataset_name)
    assert out == statistics_bytes


def test_get_system_model_statistics_dne(storage_interface, dataset_name):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_statistics(str(uuid.uuid1()), dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_statistics_wrong_owner(
    storage_interface, dataset_name, other_system_id
):
    with pytest.raises(HTTPException) as err:
        with storage_interface.start_transaction() as st:
            st.get_system_model_statistics(other_system_id, dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_timeseries_empty(
    storage_interface,
    dataset_name,
    system_id,
):
    with storage_interface.start_transaction() as st:
        st.update_system_model_data(system_id, dataset_name, None, None, None)
        with pytest.raises(HTTPException) as err:
            st.get_system_model_timeseries(system_id, dataset_name)
    assert err.value.status_code == 404


def test_get_system_model_stats_empty(
    storage_interface,
    dataset_name,
    system_id,
):
    with storage_interface.start_transaction() as st:
        st.update_system_model_data(system_id, dataset_name, None, None, None)
        with pytest.raises(HTTPException) as err:
            st.get_system_model_statistics(system_id, dataset_name)
    assert err.value.status_code == 404


@pytest.fixture()
def compute_management_interface(mocker):
    mocker.patch(
        "esprr_api.storage.engine",
        new=storage.create_engine(
            "mysql+pymysql://",
            creator=storage._make_sql_connection_partial(user="qmanager"),
        ).pool,
    )
    out = storage.ComputeManagementInterface()
    out.commit = False
    return out


def test_list_system_data_status(
    compute_management_interface, system_id, dataset_name, root_conn
):
    curs = root_conn.cursor()
    curs.execute(
        "insert into system_data (system_id, dataset, version, system_hash, error) "
        "values (uuid_to_bin(%s, 1), %s, %s, %s, %s)",
        (system_id, "other", "v0.1", "", '{"error": "err"}'),
    )
    root_conn.commit()
    out = compute_management_interface.list_system_data_status()
    assert out == [
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset="other",
            status="error",
            version="v0.1",
            hash_changed=True,
        ),
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset=dataset_name,
            status="complete",
            version="v0.1",
            hash_changed=False,
        ),
    ]

    curs.execute("delete from system_data where dataset = 'other'")
    root_conn.commit()


def test_report_failure(
    compute_management_interface, root_conn, system_id, dataset_name
):
    compute_management_interface.commit = True
    msg = {"error": "uh oh"}
    compute_management_interface.report_failure(
        system_id, dataset_name, json.dumps(msg)
    )

    curs = root_conn.cursor()
    curs.execute("select error from system_data")
    assert curs.fetchone()[0] == msg
    curs.execute(
        "update system_data set error = json_array() where system_id = "
        "uuid_to_bin(%s, 1) and dataset = %s",
        (system_id, dataset_name),
    )
    root_conn.commit()
