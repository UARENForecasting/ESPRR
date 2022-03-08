import datetime as dt
import json
from uuid import UUID, uuid1


from pymysql.err import OperationalError, IntegrityError, DataError
import pytest


def test_user_foreign_key(cursor, group_id, user_id):
    cursor.execute("select 1 from system_groups where id = uuid_to_bin(%s, 1)", group_id)
    assert cursor.fetchone()[0]
    cursor.execute("delete from users where id = uuid_to_bin(%s, 1)", user_id)
    cursor.execute("select 1 from system_groups where id = uuid_to_bin(%s, 1)", group_id)
    assert len(cursor.fetchall()) == 0


def test_mapping_system_foreign_key(cursor, system_id,user_id):
    cursor.execute(
        "select 1 from system_group_mapping where system_id = uuid_to_bin(%s, 1)",
        system_id
    )
    assert cursor.fetchone()[0]
    cursor.execute(
        "delete from systems where id = uuid_to_bin(%s, 1)", system_id)
    cursor.execute(
        "select 1 from system_group_mapping where system_id = uuid_to_bin(%s, 1)",
        system_id
    )
    assert len(cursor.fetchall()) == 0


def test_mapping_group_foreign_key(cursor, group_id,user_id):
    cursor.execute(
        "select 1 from system_group_mapping where group_id = uuid_to_bin(%s, 1)",
        group_id
    )
    assert cursor.fetchone()[0]
    cursor.execute(
        "delete from system_groups where id = uuid_to_bin(%s, 1)", group_id)
    cursor.execute(
        "select 1 from system_group_mapping where group_id = uuid_to_bin(%s, 1)",
        group_id
    )
    assert len(cursor.fetchall()) == 0


def test_get_system_group(cursor, auth0_id, group_id, group_name, user_id):
    cursor.execute(f'call get_system_group("{auth0_id}", "{group_id}")')
    res = cursor.fetchone()
    assert res[0] == group_id
    assert res[1] == user_id
    assert res[2] == group_name
    assert res[3] <= dt.datetime.utcnow()
    assert res[4] <= dt.datetime.utcnow()


def test_get_system_group_dne(cursor, auth0_id):
    group_id = uuid1()
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call get_system("{auth0_id}", "{group_id}")')
    assert err.value.args[0] == 1142


def test_get_system_group_bad_user(cursor, system_id, bad_user):
    auth0_id = bad_user
    with pytest.raises(OperationalError) as err:
        cursor.execute(f'call get_system("{auth0_id}", "{system_id}")')
    assert err.value.args[0] == 1142


def test_list_system_groups(cursor, auth0_id, group_id, system_def, user_id):
    cursor.execute(f'call list_system_groups("{auth0_id}")')
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0][0] == group_id
    assert res[0][1] == user_id


def test_list_system_groups_none(cursor, bad_user):
    cursor.execute(f'call list_system_groups("{bad_user}")')
    assert len(cursor.fetchall()) == 0


def test_create_system_group(cursor, auth0_id, user_id):
    group_name = "Another Group"
    num = cursor.execute(
        "call create_system_group(%s, %s)", (auth0_id, group_name)
    )
    assert num == 1
    id_ = cursor.fetchone()[0]
    UUID(id_)
    cursor.execute(
        "select bin_to_uuid(user_id, 1), name from system_groups where "
        "id = uuid_to_bin(%s, 1)",
        id_,
    )
    res = cursor.fetchone()
    assert res[0] == user_id
    assert res[1] == group_name


def test_create_system_group_bad_user(cursor):
    with pytest.raises(IntegrityError) as err:
        cursor.execute(
            "call create_system_group(%s, %s)", ("invalid", "another group")
        )
    assert err.value.args[0] == 1048


def test_create_system_group_duplicate_name(cursor, group_name, auth0_id):
    with pytest.raises(IntegrityError) as err:
        cursor.execute("call create_system_group(%s, %s)", (auth0_id, group_name))
    assert err.value.args[0] == 1062


def test_create_system_group_long_name(cursor, auth0_id):
    name = "a sys group" * 50
    with pytest.raises(DataError) as err:
        cursor.execute("call create_system_group(%s, %s)", (auth0_id, name))
    assert err.value.args[0] == 1406


def test_add_system_to_group(cursor, auth0_id, group_id, system_def):
    num = cursor.execute(
        "call create_system(%s, %s, %s)", (auth0_id, "Another system", system_def[1])
    )
    assert num == 1
    new_system_id = cursor.fetchone()[0]
    cursor.execute(
        "call add_system_to_group(%s, %s, %s)", (auth0_id, new_system_id, group_id)
    )
    num = cursor.execute(
        "select bin_to_uuid(system_id, 1), bin_to_uuid(group_id, 1) from system_group_mapping where system_id = uuid_to_bin(%s, 1)",
        new_system_id,
    )
    assert num == 1
    res = cursor.fetchone()
    assert res[0] == new_system_id
    assert res[1] == group_id


def test_add_system_to_group_no_access(cursor, auth0_id, group_id, system_def):
    num = cursor.execute(
        "call create_system(%s, %s, %s)", ("auth0|otheruser", "Another system", system_def[1])
    )
    assert num == 1
    new_system_id = cursor.fetchone()[0]
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            "call add_system_to_group(%s, %s, %s)", (auth0_id, new_system_id, group_id)
        )
    assert err.value.args[0] == 1142


# BELOW ARE COPIED SYSTEM TESTS FOR REFERENCE THAT HAVE NOT  YET BEEN ADJUSTED
def test_update_system_same_name(cursor, system_id, auth0_id, system_def):
    old_name = system_def[0]
    cursor.execute("select count(name) from systems where name = %s", old_name)
    assert len(cursor.fetchall()) == 1
    cursor.execute("call create_system(%s, %s, %s)", (auth0_id, "aname", system_def[1]))
    sysid = cursor.fetchone()[0]
    with pytest.raises(IntegrityError) as err:
        cursor.execute(
            "call update_system(%s, %s, %s, %s)", (auth0_id, sysid, old_name, "{}")
        )
    assert err.value.args[0] == 1062


def test_update_system_bad_user(cursor, system_id, bad_user):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            "call update_system(%s, %s, %s, %s)",
            (bad_user, system_id, "A System", "{}"),
        )
    assert err.value.args[0] == 1142


def test_update_system_bad_json(cursor, system_id, auth0_id):
    with pytest.raises(OperationalError) as err:
        cursor.execute(
            "call update_system(%s, %s, %s, %s)", (auth0_id, system_id, "A System", "{")
        )
    assert err.value.args[0] == 3140


def test_delete_system(cursor, system_id, auth0_id):
    assert (
        cursor.execute("select 1 from systems where id = uuid_to_bin(%s, 1)", system_id)
        == 1
    )
    cursor.execute("call delete_system(%s, %s)", (auth0_id, system_id))
    assert (
        cursor.execute("select 1 from systems where id = uuid_to_bin(%s, 1)", system_id)
        == 0
    )


def test_delete_system_bad_user(cursor, system_id, bad_user):
    assert (
        cursor.execute("select 1 from systems where id = uuid_to_bin(%s, 1)", system_id)
        == 1
    )
    with pytest.raises(OperationalError) as err:
        cursor.execute("call delete_system(%s, %s)", (bad_user, system_id))
    assert err.value.args[0] == 1142
    assert (
        cursor.execute("select 1 from systems where id = uuid_to_bin(%s, 1)", system_id)
        == 1
    )


def test_delete_system_bad_id(cursor, auth0_id):
    with pytest.raises(OperationalError) as err:
        cursor.execute("call delete_system(%s, %s)", (auth0_id, str(uuid1())))
    assert err.value.args[0] == 1142


def test_get_system_hash(cursor, auth0_id, system_id, system_hash):
    cursor.execute(f'call get_system_hash("{auth0_id}", "{system_id}")')
    out = cursor.fetchone()[0]
    assert out == system_hash
