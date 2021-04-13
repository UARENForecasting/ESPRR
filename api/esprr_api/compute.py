from uuid import UUID


import pandas as pd
from pvlib.location import Location  # type: ignore
from pvlib.pvsystem import PVSystem  # type: ignore
from pvlib.tracking import SingleAxisTracker  # type: ignore
from pvlib.modelchain import ModelChain  # type: ignore


from . import models
from .data.nsrdb import NSRDBDataset


def compute_ac_power(system: models.PVSystem, data: models.SystemData) -> pd.Series:
    """Compute the AC power for a system at the location and with weather from the
    background dataset
    """
    location = Location(**data.location.dict())
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
    return ac


def compute_total_system_power(
    system: models.PVSystem, dataset: NSRDBDataset
) -> pd.Series:
    """Compute the total AC power from the weather data and fractional capacity of each grid
    box the system contains"""
    out: pd.Series[float] = pd.Series([], name="ac", dtype="float64")  # type: ignore
    for data in dataset.generate_data(system):
        part = compute_ac_power(system, data)
        if out.empty:  # type: ignore
            out = part
        else:
            out += part
    return out


def run_job(system_id: UUID, dataset_name: models.DatasetEnum, user: str):
    pass
