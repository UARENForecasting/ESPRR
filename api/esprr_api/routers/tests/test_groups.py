"""Test some select system endpoint interaction. The majority of testing
is done via schemathesis in ../../tests/test_app.py
"""
from copy import deepcopy
from io import BytesIO
import json
import string
from urllib.parse import quote
import uuid


from fastapi import HTTPException
import pandas as pd
import pytest
from rq import SimpleWorker


from esprr_api import models, storage
from esprr_api.routers import groups


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

def test_add_system_to_group(client, group_id, other_system_id):
    pass
