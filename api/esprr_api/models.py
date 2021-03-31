import datetime as dt
from typing import Any, Union


import pvlib  # type: ignore
from pydantic import BaseModel, Field
from pydantic.fields import Undefined
from pydantic.types import UUID
import pytz


SYSTEM_ID = "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9"
SYSTEM_EXAMPLE = dict(
    name="Test PV System",
    nw_corner=[34.9, -112.9],
    se_corner=[33.0, -111.0],
    ac_capacity=10.0,
    ac_dc_ratio=0.8,
    per_inverter_ac_capacity=1.0,
    tracking=dict(
        tilt=20.0,
        azimuth=180.0,
    ),
)
# all compatible with luxon 1.25.0, most commen + Etc/GMT+offset
TIMEZONES = [
    tz
    for tz in pytz.common_timezones
    if not tz.startswith("US/") and tz not in ("America/Nuuk", "Antarctica/McMurdo")
] + [tz for tz in pytz.all_timezones if tz.startswith("Etc/GMT") and tz != "Etc/GMT0"]
SURFACE_ALBEDOS = pvlib.irradiance.SURFACE_ALBEDOS


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


class LatLon(ThisBase):
    latitude: float = Field(
        ..., description="Latitude of the system in degrees North", ge=24, le=50
    )
    longitude: float = Field(
        ..., description="Longitude of the system in degrees East", ge=-126, le=-65
    )


class BoundingBox(ThisBase):
    """Bounding box of the PV array"""

    nw_corner: LatLon = Field(..., description="NW corner of the bounding box.")
    se_corner: LatLon = Field(..., description="SE corner of the bounding box.")


class PVSystem(ThisBase):
    """Parameters for an entire PV system at some location"""

    name: str = UserString(
        ...,
        description="Name of the system",
    )
    boundary: BoundingBox
    # find central lat/lons and lookup elevation from lat/lon
    ac_capacity: float = Field(
        ..., description="Total AC capcity of the plant in MW", gt=0
    )
    dc_ac_ratio: float = Field(..., description="Ratio of DC to AC capacity ", gt=0)
    # split into multiple inverters based on capacity and location
    # losses all set
    albedo: float = Field(
        ..., description="Albedo of the surface around the array", ge=0
    )
    tracking: Union[FixedTracking, SingleAxisTracking] = Field(
        ..., description="Parameters describing single-axis tracking or fixed mounting"
    )
    per_inverter_ac_capacity: float = Field(
        1.0, description="Rated AC capacity for each inverter", gt=0
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
