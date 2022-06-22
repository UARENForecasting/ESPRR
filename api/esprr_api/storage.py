"""Connect to and read data from the database.


A number of functions are adapted from the Solar Forecast Arbiter with
the following license:

MIT License

Copyright (c) 2018 SolarArbiter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
from contextlib import contextmanager
import datetime as dt
from functools import partial
import json
from typing import List, Callable, Dict, Any, Union, Optional
from uuid import UUID


from fastapi import Depends, HTTPException
import pandas as pd
import pymysql
from pymysql import converters
import pytz
from sqlalchemy.engine import create_engine  # type: ignore
from sqlalchemy.pool import QueuePool  # type: ignore


from . import settings, models, __version__
from .auth import get_user_id


# this is faster than using strftime
TIMEFORMAT = "'{0.year:04}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}'"  # NOQA


def escape_timestamp(value, mapping=None):
    # adapted from the SolarForecastArbiter API under the above MIT license
    if value.tzinfo is not None:
        return TIMEFORMAT.format(value.tz_convert("UTC"))
    else:
        return TIMEFORMAT.format(value)


def escape_datetime(value, mapping=None):
    # adapted from the SolarForecastArbiter API under the above MIT license
    if value.tzinfo is not None:
        return TIMEFORMAT.format(value.astimezone(dt.timezone.utc))
    else:
        return TIMEFORMAT.format(value)


def convert_datetime_utc(obj):
    # adapted from the SolarForecastArbiter API under the above MIT license
    unlocalized = converters.convert_datetime(obj)
    return pytz.utc.localize(unlocalized)


def _make_sql_connection_partial(
    host=None, port=None, user=None, password=None, database=None
):
    # adapted from the SolarForecastArbiter API under the above MIT license
    conv = converters.conversions.copy()
    # either convert decimals to floats, or add decimals to schema
    conv[converters.FIELD_TYPE.DECIMAL] = float
    conv[converters.FIELD_TYPE.NEWDECIMAL] = float
    conv[converters.FIELD_TYPE.TIMESTAMP] = convert_datetime_utc
    conv[converters.FIELD_TYPE.DATETIME] = convert_datetime_utc
    conv[converters.FIELD_TYPE.JSON] = json.loads
    conv[UUID] = converters.escape_str
    conv[pd.Timestamp] = escape_timestamp
    conv[dt.datetime] = escape_datetime
    connect_kwargs = {
        "host": host or settings.mysql_host,
        "port": port or settings.mysql_port,
        "user": user or settings.mysql_user,
        "password": password or settings.mysql_password,
        "database": database or settings.mysql_database,
        "binary_prefix": True,
        "conv": conv,
        "use_unicode": True,
        "charset": "utf8mb4",
        "init_command": "SET time_zone = '+00:00'",
    }
    if settings.mysql_use_ssl:
        connect_kwargs["ssl"] = {"ssl": True}
    getconn = partial(pymysql.connect, **connect_kwargs)
    return getconn


engine = create_engine(
    "mysql+pymysql://",
    creator=_make_sql_connection_partial(),
    poolclass=QueuePool,
    pool_recycle=3600,
    pool_pre_ping=True,
).pool


def ensure_user_exists(f: Callable) -> Callable:
    """Decorator that ensures the DB user exists for the current auth0 ID.
    Only necessary on methods that require an existing user like create_*.
    """

    def wrapper(cls, *args, **kwargs):
        cls.create_user_if_not_exists()
        return f(cls, *args, **kwargs)

    return wrapper


class StorageTransactionError(Exception):
    """Errors raised in StorageInterface from missing method calls needed
    to complete a transaction"""

    pass


class StorageInterface:
    def __init__(self, user: str = Depends(get_user_id)):
        self.user = user
        self._cursor = None
        self.commit = True

    @property
    def cursor(self):
        if self._cursor is None:
            raise AttributeError("Cursor is only available within `start_transaction`")
        return self._cursor

    @contextmanager
    def start_transaction(self):
        connection = engine.connect()
        cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
        self._cursor = cursor
        self._add_job_result_called = False
        self._final_job_status_set = False
        try:
            yield self
        except Exception:
            connection.rollback()
            raise
        else:
            if self.commit:
                connection.commit()
        finally:
            connection.close()
        self._cursor = None

    def try_query(self, query, args):
        # adapted from the SolarForecastArbiter API under the above MIT license
        try:
            self.cursor.execute(query, args)
        except (
            pymysql.err.OperationalError,
            pymysql.err.IntegrityError,
            pymysql.err.InternalError,
            pymysql.err.DataError,
        ) as err:
            ecode = err.args[0]
            msg = err.args[1]
            if ecode == 1142:
                raise HTTPException(status_code=404, detail=msg)
            elif ecode == 1062 or ecode == 1348:
                raise HTTPException(status_code=409, detail=msg)
            elif ecode == 3140 or ecode == 1406 or ecode == 1048 or ecode == 1054:
                raise HTTPException(status_code=400, detail=msg)
            else:
                raise

    def _call_procedure(
        self,
        procedure_name: str,
        *args,
        with_current_user: bool = True,
    ) -> dict:
        """
        Can't user callproc since it doesn't properly use converters.
        Will not handle OUT or INOUT parameters without first setting
        local variables and retrieving from those variables
        """
        # adapted from the SolarForecastArbiter API under the above MIT license
        if with_current_user:
            new_args = (self.user, *args)
        else:
            new_args = args
        query = f'CALL {procedure_name}({",".join(["%s"] * len(new_args))})'
        self.try_query(query, new_args)
        out: dict = self.cursor.fetchall()
        return out

    def _call_procedure_for_single(
        self,
        procedure_name: str,
        *args,
        with_current_user: bool = True,
    ) -> dict:
        """Wrapper handling try/except logic when a single value is expected"""
        # adapted from the SolarForecastArbiter API under the above MIT license
        try:
            result: dict = self._call_procedure(
                procedure_name,
                *args,
                with_current_user=with_current_user,
            )[0]
        except IndexError:
            raise HTTPException(status_code=404)
        return result

    def create_user_if_not_exists(self) -> str:
        out: str = self._call_procedure_for_single("create_user_if_not_exists")[
            "user_id"
        ]
        return out

    @ensure_user_exists
    def get_user(self) -> models.UserInfo:
        out = self._call_procedure_for_single("get_user")
        out["object_id"] = out.pop("user_id")
        out["object_type"] = "user"
        out["modified_at"] = out["created_at"]
        return models.UserInfo(**out)

    def _parse_system(self, sys: Dict[str, Any]) -> models.StoredPVSystem:
        sys["object_id"] = sys.pop("system_id")
        sys["object_type"] = "system"
        return models.StoredPVSystem(**sys)

    def list_systems(self) -> List[models.StoredPVSystem]:
        systems = self._call_procedure("list_systems")
        out = []
        for sys in systems:
            out.append(self._parse_system(sys))
        return out

    @ensure_user_exists
    def create_system(self, system_def: models.PVSystem) -> models.StoredObjectID:
        created = self._call_procedure_for_single(
            "create_system", system_def.name, system_def.json()
        )
        return models.StoredObjectID(
            object_id=created["system_id"], object_type="system"
        )

    def get_system(self, system_id: UUID) -> models.StoredPVSystem:
        system = self._call_procedure_for_single("get_system", system_id)
        return self._parse_system(system)

    def delete_system(self, system_id: UUID):
        self._call_procedure("delete_system", system_id)

    def update_system(
        self, system_id: UUID, system_def: models.PVSystem
    ) -> models.StoredObjectID:
        self._call_procedure(
            "update_system", system_id, system_def.name, system_def.json()
        )
        return models.StoredObjectID(object_id=system_id, object_type="system")

    def get_system_hash(self, system_id: UUID) -> str:
        out: str = self._call_procedure_for_single("get_system_hash", system_id)[
            "system_hash"
        ]
        return out

    @ensure_user_exists
    def create_system_model_data(self, system_id: UUID, dataset: models.DatasetEnum):
        self._call_procedure("create_system_data", system_id, dataset)

    def get_system_model_meta(
        self, system_id: UUID, dataset: models.DatasetEnum
    ) -> models.SystemDataMeta:
        out = self._call_procedure_for_single(
            "get_system_data_meta", system_id, dataset
        )
        stored_hash = out.pop("system_hash")
        if stored_hash is not None:
            current_hash = self.get_system_hash(system_id)
            out["system_modified"] = stored_hash.lower() != current_hash
        else:
            out["system_modified"] = False
        # present "prepared" status as "queued"
        if out["status"] == "prepared":
            out["status"] = "queued"
        return models.SystemDataMeta(**out)

    def update_system_model_data(
        self,
        system_id: UUID,
        dataset: models.DatasetEnum,
        system_hash: str,
        timeseries_data: Optional[bytes],
        statistics: Optional[bytes],
        error: Union[dict, List[dict]] = [],
    ):
        self._call_procedure(
            "update_system_data",
            system_id,
            dataset,
            timeseries_data,
            statistics,
            json.dumps(error),
            __version__,
            system_hash,
        )

    def get_system_model_timeseries(
        self, system_id: UUID, dataset: models.DatasetEnum
    ) -> bytes:
        res = self._call_procedure_for_single(
            "get_system_timeseries", system_id, dataset
        )
        if res["timeseries"] is None:
            raise HTTPException(status_code=404, detail="No timeseries data available")
        out: bytes = res["timeseries"]
        return out

    def get_system_model_statistics(
        self, system_id: UUID, dataset: models.DatasetEnum
    ) -> bytes:
        res = self._call_procedure_for_single(
            "get_system_statistics", system_id, dataset
        )
        if res["statistics"] is None:
            raise HTTPException(status_code=404, detail="No statistics available")
        out: bytes = res["statistics"]
        return out

    @ensure_user_exists
    def create_system_group(self, name: str):
        created = self._call_procedure_for_single("create_system_group", name)
        return models.StoredObjectID(
            object_id=created["group_id"], object_type="system_group"
        )

    def update_system_group(self, group_id: UUID, name: str):
        self._call_procedure("update_system_group", group_id, name)
        return models.StoredObjectID(object_id=group_id, object_type="system_group")

    def delete_system_group(self, group_id: UUID):
        self._call_procedure("delete_system_group", group_id)

    def _parse_system_group(self, group, group_systems=None):
        definition = {"name": group.pop("name")}
        if group_systems is not None:
            # systems are an optional field, so that when we're listing
            # groups, we don't have to make so many calls
            systems = [self._parse_system(sys) for sys in group_systems]
            definition["systems"] = systems
        group["object_id"] = group.pop("group_id")
        group["object_type"] = "system_group"
        group["definition"] = definition
        return models.StoredSystemGroup(**group)

    def get_system_group(self, group_id: UUID):
        group = self._call_procedure_for_single("get_system_group", group_id)
        group_systems = self._call_procedure("get_group_systems", group_id)
        return self._parse_system_group(group, group_systems)

    def list_system_groups(self):
        groups = self._call_procedure("list_system_groups")
        out = []
        for group in groups:
            out.append(self._parse_system_group(group))
        return out

    def add_system_to_group(self, system_id: UUID, group_id: UUID):
        self._call_procedure("add_system_to_group", system_id, group_id)

    def remove_system_from_group(self, system_id: UUID, group_id: UUID):
        self._call_procedure("remove_system_from_group", system_id, group_id)


class ComputeManagementInterface(StorageInterface):
    """A special interface to the database (that requires different permissions)
    to list all computations and allow setting a failure message on a computation.
    """

    def __init__(self):
        self._cursor = None
        self.commit = True

    def list_system_data_status(self) -> List[models.ManagementSystemDataStatus]:
        with self.start_transaction() as st:
            res = st._call_procedure("list_system_data_status", with_current_user=False)

        def repq(d):
            if d["status"] == "prepared":
                d["status"] = "queued"
            return d

        return [models.ManagementSystemDataStatus(**repq(r)) for r in res]

    def report_failure(self, system_id: str, dataset: str, message: str):
        with self.start_transaction() as st:
            st._call_procedure(
                "report_failure", system_id, dataset, message, with_current_user=False
            )
