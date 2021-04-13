import datetime as dt
import json
import logging
import time
from typing import Union, Type, Dict, Tuple, List
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

    def enqueue_job(
        self,
        system_id: Union[UUID, str],
        dataset: Union[models.DatasetEnum, str],
        user: str,
    ) -> Type[Job]:
        # check if job already exists
        key = self.generate_key(system_id, dataset)
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
