def test_list_system_data_status(dictcursor, system_id):
    dictcursor.execute(
        "update system_data set system_hash = unhex(md5('a')) where system_id = uuid_to_bin(%s, 1) and dataset = 'timeseries missing'",
        system_id,
    )
    dictcursor.execute("call list_system_data_status()")
    out = dictcursor.fetchall()
    assert len(out) == 5
    for o in out:
        assert o["system_id"] == system_id
        assert o["status"] == o["dataset"]
        if o["dataset"] == "timeseries missing":
            assert o["hash_changed"]
        else:
            assert not o["hash_changed"]
        assert "version" in o


def test_report_failure(dictcursor, system_id):
    dictcursor.execute(
        "select error from system_data where system_id = uuid_to_bin(%s, 1) and dataset = 'prepared'",
        system_id,
    )
    assert dictcursor.fetchone()["error"] == "{}"
    dictcursor.execute(
        "call report_failure(%s, 'prepared', %s)", (system_id, '{"error": "i failed"}')
    )
    dictcursor.execute(
        "select error from system_data where system_id = uuid_to_bin(%s, 1) and dataset = 'prepared'",
        system_id,
    )
    assert dictcursor.fetchone()["error"] == '{"error": "i failed"}'
