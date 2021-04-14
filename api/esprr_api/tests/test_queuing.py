import pytest
from rq import Queue, get_current_job, SimpleWorker
from rq.exceptions import NoSuchJobError
from rq.job import Job


from esprr_api import queuing


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
