import datetime as dt
from enum import Enum
from typing import Union, List, Optional, Any, Tuple, Dict


import pandas as pd
import pvlib  # type: ignore
from pydantic import BaseModel, Field, PrivateAttr, validator, root_validator
from pydantic.fields import Undefined
from pydantic.types import UUID
import pytz


SYSTEM_ID = "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9"
SYSTEM_EXAMPLE = dict(
    name="Test PV System",
    latitude=33.98,
    longitude=-115.323,
    elevation=2300,
    inverters=[
        dict(
            name="Inverter 1",
            make_model="ABB__MICRO_0_25_I_OUTD_US_208__208V_",
            inverter_parameters=dict(
                Pso=2.08961,
                Paco=250,
                Pdco=259.589,
                Vdco=40,
                C0=-4.1e-05,
                C1=-9.1e-05,
                C2=0.000494,
                C3=-0.013171,
                Pnt=0.075,
            ),
            losses={},
            arrays=[
                dict(
                    name="Array 1",
                    make_model="Canadian_Solar_Inc__CS5P_220M",
                    albedo=0.2,
                    modules_per_string=7,
                    strings=5,
                    tracking=dict(
                        tilt=20.0,
                        azimuth=180.0,
                    ),
                    temperature_model_parameters=dict(
                        u_c=29.0, u_v=0.0, eta_m=0.1, alpha_absorption=0.9
                    ),
                    module_parameters=dict(
                        alpha_sc=0.004539,
                        gamma_ref=1.2,
                        mu_gamma=-0.003,
                        I_L_ref=5.11426,
                        I_o_ref=8.10251e-10,
                        R_sh_ref=381.254,
                        R_s=1.06602,
                        R_sh_0=400.0,
                        cells_in_series=96,
                    ),
                )
            ],
            airmass_model="kastenyoung1989",
            aoi_model="physical",
            clearsky_model="ineichen",
            spectral_model="no_loss",
            transposition_model="haydavies",
        )
    ],
)
# all compatible with luxon 1.25.0, most commen + Etc/GMT+offset
TIMEZONES = [
    tz
    for tz in pytz.common_timezones
    if not tz.startswith("US/") and tz not in ("America/Nuuk", "Antarctica/McMurdo")
] + [tz for tz in pytz.all_timezones if tz.startswith("Etc/GMT") and tz != "Etc/GMT0"]
SURFACE_ALBEDOS = pvlib.irradiance.SURFACE_ALBEDOS
TEMPERATURE_PARAMETERS = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS


# allows word chars, space, comma, apostrophe, hyphen, parentheses, underscore
# and empty string
def UserString(default: Any = Undefined, *, title: str = None, description: str = None):
    return Field(
        default,
        title=title,
        description=description,
        max_length=128,
        regex=r"^(?!\W+$)(?![_ ',\-\(\)]+$)[\w ',\-\(\)]*$",
    )


class ThisBase(BaseModel):
    class Config:
        extra = "forbid"


class FixedTracking(ThisBase):
    """Parameters for a fixed tilt array"""

    tilt: float = Field(
        ..., description="Tilt of modules in degrees from horizontal", ge=0, le=180
    )
    azimuth: float = Field(
        ...,
        description="Azimuth of modules relative to North in degrees",
        ge=0,
        lt=360.0,
    )


class SingleAxisTracking(ThisBase):
    """Parameters for a single axis tracking array"""

    axis_tilt: float = Field(
        ...,
        title="Axis Tilt",
        description="Tilt of tracker axis in degrees from horizontal",
        ge=0,
        le=90,
    )
    axis_azimuth: float = Field(
        ...,
        title="Axis Azimiuth",
        description="Azimuth of tracker axis clockwise from North in degrees",
        ge=0,
        lt=360.0,
    )
    gcr: float = Field(
        ...,
        title="GCR",
        description=(
            "Ground coverage ratio: ratio of module length to the spacing"
            " between trackers"
        ),
        ge=0,
    )
    backtracking: bool = Field(
        ..., description="True if the tracking system supports backtracking"
    )


class PVSystem(ThisBase):
    """Parameters for an entire PV system at some location"""

    name: str = UserString(
        ...,
        description="Name of the system",
    )
    # use w/ boxes from dataset to
    corners: Tuple[Tuple[float, float], Tuple[float, float]] = Field(
        ..., description='')
    # find central lat/lons and lookup elevation from lat/lon
    ac_capacity: float
    ac_dc_ratio: float
    # split into multiple inverters based on capacity and location
    # use a typical value 1.0 to maybe 5
    per_inverter_ac_capacity: float = 1.0 # MW
    # losses all set
    # albedo?
    tracking: Union[FixedTracking, SingleAxisTracking] = Field(
        ..., description="Parameters describing single-axis tracking or fixed mounting"
    )

    class Config:
        schema_extra = {"example": SYSTEM_EXAMPLE}


class StoredObjectID(ThisBase):
    object_id: UUID = Field(..., description="Unique identifier of the object")
    object_type: str = Field("system", description="Type of the object")

    class Config:
        # allow extra fields to go into Stored objects as they are
        # removed when serializing. Eases putting DB objects into models
        extra = "ignore"
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
            }
        }


class StoredObject(StoredObjectID):
    created_at: dt.datetime = Field(..., description="Datetime the object was created")
    modified_at: dt.datetime = Field(
        ..., description="Datetime the object was last modified"
    )

    class Config:
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
                "created_at": "2020-12-01T01:23:00+00:00",
                "modified_at": "2020-12-01T01:23:00+00:00",
            }
        }


class StoredPVSystem(StoredObject):

    definition: PVSystem

    class Config:
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
                "created_at": "2020-12-01T01:23:00+00:00",
                "modified_at": "2020-12-01T01:23:00+00:00",
                "definition": SYSTEM_EXAMPLE,
            }
        }


class UserInfo(StoredObject):
    """Information about the current user"""

    auth0_id: str = Field(..., description="User ID from Auth 0")
