from uuid import UUID


from dask.base import tokenize  # type: ignore
from fastapi import HTTPException
import pandas as pd
from pvlib.location import Location  # type: ignore
from pvlib.pvsystem import PVSystem  # type: ignore
from pvlib.tracking import SingleAxisTracker  # type: ignore
from pvlib.modelchain import ModelChain  # type: ignore


from . import models, storage, utils
from .data.nsrdb import NSRDBDataset


class CachedLocation(Location):
    """
    Cache the solar position data and avoid recomputing multiple times
    """

    _stored_solpos = (None, None)

    def get_solarposition(self, times, *args, **kwargs):
        # cant use functools since datetimeindex not hashable
        # dask has a nice tokenize function for hashing
        if (key := tokenize(times, *args, **kwargs)) != self._stored_solpos[0]:
            solpos = super().get_solarposition(times, *args, **kwargs)
            self._stored_solpos = (key, solpos)
        return self._stored_solpos[1].copy()


def compute_single_location(
    system: models.PVSystem, data: models.SystemData
) -> pd.DataFrame:
    """Compute the AC power and clearsky power for a system at the location and with weather
    from the background dataset
    """
    location = CachedLocation(**data.location.dict())
    fractional_capacity = system.ac_capacity * data.fraction_of_total
    eta = 0.96
    pvsyst_params = dict(
        albedo=system.albedo,
        module_type="glass_polymer",
        racking_model="open_rack",
        module_parameters=dict(
            gamma_pdc=-0.003,
            pdc0=fractional_capacity * system.dc_ac_ratio,
        ),
        inverter_parameters=dict(
            pdc0=fractional_capacity / eta,
            eta_inv_nom=eta,
        ),
    )

    if isinstance(system.tracking, models.SingleAxisTracking):
        pvsystem = SingleAxisTracker(
            **pvsyst_params,
            axis_tilt=system.tracking.axis_tilt,
            axis_azimuth=system.tracking.axis_azimuth,
            gcr=system.tracking.gcr,
            backtrack=system.tracking.backtracking,
        )
    else:
        pvsystem = PVSystem(
            **pvsyst_params,
            surface_tilt=system.tracking.tilt,
            surface_azimuth=system.tracking.azimuth,
        )

    mc = ModelChain.with_pvwatts(system=pvsystem, location=location)
    mc.run_model(data.weather_data)
    ac: pd.Series = mc.results.ac

    clr_mc = ModelChain.with_pvwatts(system=pvsystem, location=location)
    clr_mc.run_model(data.clearsky_data)
    clr_ac: pd.Series = clr_mc.results.ac

    out = pd.DataFrame({"ac_power": ac, "clearsky_ac_power": clr_ac})
    out.index.name = "time"  # type: ignore
    return out


def compute_total_system_power(
    system: models.PVSystem, dataset: NSRDBDataset
) -> pd.DataFrame:
    """Compute the total AC power from the weather data and fractional capacity of each grid
    box the system contains"""
    out: pd.DataFrame = pd.DataFrame(
        [],
        columns=["ac_power", "clearsky_ac_power"],
        index=pd.DatetimeIndex([], name="time"),  # type: ignore
        dtype="float64",
    )
    for data in dataset.generate_data(system):
        part = compute_single_location(system, data)
        if out.empty:  # type: ignore
            out = part
        else:
            out += part  # type: ignore
    return out


def _get_dataset(dataset_name: models.DatasetEnum) -> NSRDBDataset:
    # will take about two seconds to load grid, could possibly preload
    # before the RQ fork, but not worth it for now
    ds = NSRDBDataset()
    ds.load_grid()
    return ds


def run_job(system_id: UUID, dataset_name: models.DatasetEnum, user: str):
    si = storage.StorageInterface(user=user)
    with si.start_transaction() as st:
        try:
            system = st.get_system(system_id)
            syshash = st.get_system_hash(system_id)
        except HTTPException as err:
            if err.status_code == 404:
                return
            else:  # pragma: no cover
                raise
    dataset = _get_dataset(dataset_name)
    ac_power = compute_total_system_power(system.definition, dataset)
    ac_bytes = utils.dump_arrow_bytes(
        utils.convert_to_arrow(ac_power.reset_index())
    )  # type: ignore
    stats_bytes = utils.dump_arrow_bytes(utils.convert_to_arrow(pd.DataFrame()))
    with si.start_transaction() as st:
        st.update_system_model_data(
            system_id, dataset_name, syshash, ac_bytes, stats_bytes
        )
