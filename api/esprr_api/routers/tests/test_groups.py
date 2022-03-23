"""Test some select system endpoint interaction. The majority of testing
is done via schemathesis in ../../tests/test_app.py
"""
import pytest


from esprr_api import models


pytestmark = pytest.mark.usefixtures("add_example_db_data")


def test_list_groups(client, stored_system_group):
    response = client.get("/system_groups")
    groups = [models.StoredSystemGroup(**g) for g in response.json()]
    group = groups[0].dict()
    expected_dict = stored_system_group.copy(deep=True).dict()
    expected_dict['definition'].pop('systems')
    assert len(groups) == 1
    for key in ['object_id', 'object_type']:
        assert group[key] == expected_dict[key]


def test_get_group(client, group_id, stored_system_group):
    group = client.get(f"/system_groups/{group_id}").json()
    expected_dict = stored_system_group.dict()

    assert group['object_id'] == str(expected_dict['object_id'])
    assert group['object_type'] == expected_dict['object_type']

    group_def = group['definition']
    expected_def = expected_dict['definition']

    assert len(group_def['systems']) == 1

    group_sys = group_def['systems'][0]
    expected_sys = expected_def['systems'][0]

    assert group_sys['object_id'] == str(expected_sys['object_id'])


def test_get_group_dne(client, system_id, stored_system_group):
    group = client.get(f"/system_groups/{system_id}")
    assert group.status_code == 404


def test_create_delete_group(client):
    groups = client.get("system_groups/").json()
    assert len(groups) == 1
    new = client.post(
        "/system_groups/",
        json={"name": "I'm a new group"}
    )
    assert new.status_code == 201
    new_group = client.get(new.headers['Location'])
    assert new_group.status_code == 200
    ng = new_group.json()
    assert ng['definition']['name'] == "I'm a new group"
    assert ng['definition']['systems'] == []
    groups = client.get("system_groups/").json()
    assert len(groups) == 2
    delete = client.delete(new.headers['Location'])
    assert delete.status_code == 204
    groups = client.get("/system_groups/").json()
    assert len(groups) == 1
    group = client.get(new.headers['Location'])
    assert group.status_code == 404


def test_create_group_duplicate_name(client, group_name):
    new = client.post(
        "/system_groups/",
        json={"name": group_name}
    )
    assert new.status_code == 409


def test_delete_system_group_group_dne(client, system_id):
    delete = client.delete(f"/system_groups/{system_id}")
    assert delete.status_code == 404


def test_update_system_group(client):
    new = client.post(
        "/system_groups/",
        json={"name": "I'm a new group"}
    )
    assert new.status_code == 201
    new_group = client.get(new.headers['Location'])
    assert new_group.status_code == 200
    update = client.post(
        new.headers['Location'],
        json={"name": "I'm the old group"}
    )
    assert update.status_code == 201
    new_group = client.get(new.headers['Location'])
    ng = new_group.json()
    assert ng['definition']['name'] == "I'm the old group"
    delete = client.delete(new.headers['Location'])
    delete.status_code == 204


def test_add_system_to_group(
        client, group_id, nocommit_transaction, system_def
):
    sys_def = system_def.dict()
    sys_def['name'] = "this other one"
    new_system = client.post("/systems/", json=sys_def).json()
    sys_id = new_system['object_id']
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group['definition']['systems']) == 1
    added = client.post(
        f"/system_groups/{group_id}/systems/{sys_id}"
    )
    assert added.status_code == 201
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group['definition']['systems']) == 2
    added_name = group['definition']['systems'][1]['definition']['name']
    assert added_name == "this other one"


def test_add_system_to_group_system_dne(client, group_id, other_system_id):
    res = client.post(f"/system_groups/{group_id}/systems/{other_system_id}")
    assert res.status_code == 404


def test_add_system_to_group_group_dne(client, other_system_id, system_id):
    res = client.post(f"/system_groups/{other_system_id}/systems/{other_system_id}")
    assert res.status_code == 404


def test_remove_system_from_group(client, group_id, system_id):
    removal = client.delete(
        f"/system_groups/{group_id}/systems/{system_id}"
    )
    assert removal.status_code == 201
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group["definition"]["systems"]) == 0


def test_remove_system_from_group_system_dne(
        client, group_id, other_system_id
):
    removal = client.delete(
        f"/system_groups/{group_id}/systems/{other_system_id}"
    )
    assert removal.status_code == 404


def test_remove_system_from_group_group_dne(
        client, system_id, other_system_id
):
    removal = client.delete(
        f"/system_groups/{system_id}/systems/{other_system_id}"
    )
    assert removal.status_code == 404
