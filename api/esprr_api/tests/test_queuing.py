import pytest
from rq import Queue, get_current_job, SimpleWorker
from rq.exceptions import NoSuchJobError
from rq.job import Job


from esprr_api import queuing, models


pytestmark = pytest.mark.usefixtures("mock_redis")


def test_verify_redis_conn():
    assert queuing.verify_redis_conn()


def run(sys_id, dsname, user):
    job = get_current_job()
    # started_at not set when using sync queue
    job.started_at = job.enqueued_at
    return sys_id, dsname, user


@pytest.fixture()
def qm():
    out = queuing.QueueManager()
    out.job_func = run
    q = Queue(is_async=False, connection=out.redis_conn)
    out.q = q
    return out


def test_qmanager_enqueue_job(qm, system_id, dataset_name):
    job = qm.enqueue_job(system_id, dataset_name, "user")
    assert job.is_finished
    assert job.result == (system_id, dataset_name, "user")
    assert job.id == qm.generate_key(system_id, dataset_name)

    # if enqueued multiple times, only get first job
    job2 = qm.enqueue_job(system_id, dataset_name, "user")
    assert job2 == job


def test_qmanager_job_is_running(qm, system_id, dataset_name):
    assert not qm.job_is_running(system_id, dataset_name)
    qm.enqueue_job(system_id, dataset_name, "user")
    assert qm.job_is_running(system_id, dataset_name)


def test_qmanager_delete_job(qm, system_id, dataset_name):
    key = qm.generate_key(system_id, dataset_name)
    qm.enqueue_job(system_id, dataset_name, "user")
    # job exists
    Job.fetch(key, connection=qm.redis_conn)
    qm.delete_job(system_id, dataset_name)
    with pytest.raises(NoSuchJobError):
        Job.fetch(key, connection=qm.redis_conn)


def test_qmanager_remove_invalid_jobs(system_id):
    qm = queuing.QueueManager()
    qm.job_func = run
    current_stat = [
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset=str(i),
            version=f"v0.{i*2}",
            status={
                0: "queued",
                1: "complete",
                2: "statistics missing",
                3: "timeseries missing",
                4: "error",
            }.get(i, "complete"),
            hash_changed=i == 1,
            user="user",
        )
        for i in range(8)
    ]
    for j in current_stat:
        qm.enqueue_job(j.system_id, j.dataset, j.user)
    qm.enqueue_job(system_id, "other", "other")
    assert len(qm.q.job_ids) == 9
    qm.remove_invalid_jobs(current_stat)
    assert qm.q.job_ids == [f"{system_id}:{i}" for i in range(5)]


def test_qmanager_add_missing_jobs(system_id):
    qm = queuing.QueueManager()
    qm.job_func = run
    current_stat = [
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset=str(i),
            version=f"v0.{i*2}",
            status={
                0: "queued",
                1: "complete",
                2: "statistics missing",
                3: "timeseries missing",
                4: "error",
            }.get(i, "queued"),
            hash_changed=i in (1, 2),
            user="user",
        )
        for i in range(7)
    ]
    qm.enqueue_job(system_id, "0", "user")
    assert set(qm.q.job_ids) == {f"{system_id}:0"}
    qm.add_missing_jobs(current_stat)
    assert len(qm.q.job_ids) == 5
    assert {j.split(":")[1] for j in qm.q.job_ids} == {"0", "1", "2", "5", "6"}


def fail(err, msg):
    raise err(msg)


def ok():
    pass


def test_qmanager_evaluate_failed_jobs(system_id):
    qm = queuing.QueueManager()
    qm.job_func = fail
    assert len(qm.q.failed_job_registry) == 0
    qm.q.enqueue(fail, ValueError, "0 isnt 1", job_id="nothere")
    qm.q.enqueue(fail, ValueError, "0 isnt 1", job_id=f"{system_id}:0")
    qm.q.enqueue(fail, ValueError, "0 isnt 1", job_id=f"{system_id}:5")
    qm.q.enqueue(ok, job_id=f"{system_id}:1")
    qm.q.enqueue(fail, TypeError, "wrong type", job_id=f"{system_id}:2")
    w = SimpleWorker([qm.q], connection=qm.redis_conn)
    w.work(burst=True)
    assert len(qm.q.failed_job_registry) == 4
    current_stat = [
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset=str(i),
            version=f"v0.{i*2}",
            status={
                0: "queued",
                1: "complete",
                2: "statistics missing",
                3: "timeseries missing",
                4: "error",
            }.get(i, "queued"),
            hash_changed=i in (2, 5),
            user="user",
        )
        for i in range(7)
    ]
    out = qm.evaluate_failed_jobs(current_stat)
    assert len(out) == 1  # only 0 is queued failed and not hash change
    assert out[0][1] == "0"
    assert "error" in out[0][2]


def test_sync_jobs(system_id, mocker):
    qm = queuing.QueueManager()
    qm.job_func = run
    current_stat = [
        models.ManagementSystemDataStatus(
            system_id=system_id,
            dataset=str(i),
            version=f"v0.{i*2}",
            status={
                0: "queued",
                1: "complete",
                2: "statistics missing",
                3: "timeseries missing",
                4: "error",
            }.get(i, "queued"),
            hash_changed=i in (2, 5),
            user="user",
        )
        for i in range(7)
    ]
    qm.q.enqueue(fail, ValueError, "0 isnt 1", job_id=f"{system_id}:0")
    qm.q.enqueue(fail, ValueError, "0 isnt 1", job_id="abnormal")
    w = SimpleWorker([qm.q], connection=qm.redis_conn)
    w.work(burst=True)
    assert len(qm.q.failed_job_registry) == 2

    qm.enqueue_job(system_id, "5", "user")
    assert qm.q.job_ids == [f"{system_id}:5"]

    mocker.patch("esprr_api.queuing.time.sleep", side_effect=KeyboardInterrupt)

    jmi = mocker.MagicMock()
    startt = jmi.start_transaction.return_value.__enter__.return_value
    startt.list_system_data_status.return_value = current_stat
    mocker.patch(
        "esprr_api.queuing._get_compute_management_interface",
        return_value=jmi,
    )
    queuing.sync_jobs()
    assert startt.report_failure.call_count == 1
    assert set(qm.q.job_ids) == {f"{system_id}:2", f"{system_id}:5", f"{system_id}:6"}
