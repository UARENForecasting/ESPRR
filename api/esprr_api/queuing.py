import json
import logging
import time
from typing import Union, Type, Tuple, List
from uuid import UUID


from redis import Redis, ConnectionPool
from rq import Queue  # type: ignore
from rq.command import send_stop_job_command  # type: ignore
from rq.exceptions import NoSuchJobError  # type: ignore
from rq.job import Job  # type: ignore


from . import settings, compute, models


logger = logging.getLogger(__name__)
redis_pool = ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    username=settings.redis_username,
    password=settings.redis_password,
    health_check_interval=settings.redis_health_check_interval,
)


def _get_redis_conn():  # pragma: no cover
    # easier mocking of redis
    return Redis(connection_pool=redis_pool)


def verify_redis_conn():
    redis_conn = _get_redis_conn()
    return redis_conn.ping()


def _get_queue(name, redis_conn):
    return Queue(name, connection=redis_conn)


class QueueManager:
    def __init__(
        self,
        queue_name: str = "jobs",
    ):
        self.redis_conn = _get_redis_conn()
        self.q = _get_queue(queue_name, self.redis_conn)
        self.job_func = compute.run_job

    @property
    def registries(self):
        return [
            getattr(self.q, reg)
            for reg in (
                "started_job_registry",
                "deferred_job_registry",
                "finished_job_registry",
                "failed_job_registry",
                "scheduled_job_registry",
            )
        ]

    def generate_key(
        self, system_id: Union[UUID, str], dataset: Union[models.DatasetEnum, str]
    ) -> str:
        return f"{str(system_id)}:{dataset}"

    def decompose_key(self, inp: str) -> Tuple[str, str]:
        return inp.split(":")

    def enqueue_job(
        self,
        system_id: Union[UUID, str],
        dataset: Union[models.DatasetEnum, str],
        user: str,
    ) -> Type[Job]:
        # check if job already exists
        key = self.generate_key(system_id, dataset)
        job: Type[Job]
        try:
            job = Job.fetch(key, connection=self.redis_conn)
        except NoSuchJobError:
            job = Job.create(
                self.job_func,
                args=(system_id, dataset, user),
                id=key,
                result_ttl=0,
                timeout="10m",
                failure_ttl=3600 * 24 * 14,
                connection=self.redis_conn,
            )
            self.q.enqueue_job(job)
        return job

    def job_is_running(
        self, system_id: UUID, dataset: Union[models.DatasetEnum, str]
    ) -> bool:
        """Return if the job has been started"""
        key = self.generate_key(system_id, dataset)
        try:
            job = Job.fetch(key, connection=self.redis_conn)
        except NoSuchJobError:
            pass
        else:
            if job.started_at is not None:
                return True
        return False

    def delete_job(self, system_id: UUID, dataset: Union[models.DatasetEnum, str]):
        """Try removing the job if present in any registries"""
        key = self.generate_key(system_id, dataset)
        try:
            send_stop_job_command(self.redis_conn, key)
        except Exception:
            pass
        for registry in self.registries:
            try:
                registry.remove(key, delete_job=True)
            except Exception:
                pass

    def remove_invalid_jobs(
        self, current_status: List[models.ManagementSystemDataStatus]
    ):
        """Remove jobs from any queue that are complete or have been
        deleted from the database"""
        all_jobs = []
        jobs_to_remove_if_present = []
        for m in current_status:
            key = self.generate_key(m.system_id, m.dataset)
            all_jobs.append(key)
            if m.status == "complete" and not m.hash_changed:
                jobs_to_remove_if_present.append(key)

        i = 0
        for job_id in self.q.job_ids:
            if job_id not in all_jobs or job_id in jobs_to_remove_if_present:
                self.delete_job(*self.decompose_key(job_id))
                i += 1
        if i:
            logger.info("Removed %s invalid jobs from the queues", i)

    def add_missing_jobs(self, current_status: List[models.ManagementSystemDataStatus]):
        """Add jobs to the queue that are missing but present in the database
        and not complete"""
        i = 0
        for m in current_status:
            if (m.status == "queued" or m.hash_changed) and self.generate_key(
                m.system_id, m.dataset
            ) not in self.q.job_ids:
                self.enqueue_job(m.system_id, m.dataset, m.user)
                i += 1
        if i:
            logger.info("Enqueuing %s missing jobs", i)

    def evaluate_failed_jobs(
        self, current_status: List[models.ManagementSystemDataStatus]
    ) -> List[Tuple[str, str, str]]:
        """If job has gotten to the failed job registry, some uncaught error
        happened. Return the data needed to update errors in the db."""

        jobd = {self.generate_key(m.system_id, m.dataset): m for m in current_status}
        out = []

        for failed_job in self.q.failed_job_registry.get_job_ids():
            if failed_job not in jobd:
                self.q.failed_job_registry.remove(failed_job, delete_job=True)
            elif (
                jobd[failed_job].status == "queued"
                and not jobd[failed_job].hash_changed
            ):
                msg = json.dumps(
                    {
                        "error": {
                            "details": (
                                "Uncaught error during job execution. "
                                "Framework administrators have been notified."
                            )
                        }
                    }
                )
                out.append((jobd[failed_job].system_id, jobd[failed_job].dataset, msg))
        if lo := len(out):
            logger.info("%s jobs processed from failed job registry", lo)
        return out


def _get_compute_management_interface():  # pragma: no cover
    from .storage import ComputeManagementInterface

    return ComputeManagementInterface()


def sync_jobs():
    """Keep jobs between the RQ queue and database in sync"""
    cmi = _get_compute_management_interface()
    qm = QueueManager()

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
    while True:
        try:
            logger.info(
                "Adding missing jobs, removing invalid jobs, and "
                "cleaning up failed jobs"
            )
            # add missing jobs
            with cmi.start_transaction() as jst:
                current_status = jst.list_system_data_status()
            qm.add_missing_jobs(current_status)
            # remove invalid
            with cmi.start_transaction() as jst:
                current_status = jst.list_system_data_status()
            qm.remove_invalid_jobs(current_status)
            # cleanup failed job registry
            with cmi.start_transaction() as jst:
                most_current_status = jst.list_system_data_status()
                failed_jobs = qm.evaluate_failed_jobs(most_current_status)
                for system_id, dataset, msg in failed_jobs:
                    jst.report_failure(system_id, dataset, msg)
            time.sleep(settings.sync_jobs_period)
        except KeyboardInterrupt:
            break
