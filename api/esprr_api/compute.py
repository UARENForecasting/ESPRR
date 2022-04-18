import calendar
from uuid import UUID


from dask.base import tokenize  # type: ignore
from fastapi import HTTPException
import pandas as pd
from pvlib.location import Location  # type: ignore
from pvlib.pvsystem import PVSystem  # type: ignore
from pvlib.tracking import SingleAxisTracker  # type: ignore
from pvlib.modelchain import ModelChain  # type: ignore
from pvlib.solarposition import get_solarposition  # type: ignore
import numpy as np

from . import models, storage, utils
from .data.nsrdb import NSRDBDataset, find_dataset_path


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
            gamma_pdc=-0.004,
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
            max_angle=50.0,
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

    # hack to make output more consistent with actuals in not-clear conditions
    clear = out["ac_power"] > 0.99 * out["clearsky_ac_power"]

    multiplier = calculate_variable_multiplier(out)

    # apply multiplier to ac_power
    out["ac_power"] = out["ac_power"].where(
        clear, other=out["ac_power"] * multiplier.reindex(clear.index).ffill()
    )  # type: ignore

    return out


def calculate_variable_multiplier(out):
    """
    Calculate a multiplier that varies given daily standard deviation of
    irradiance.

    Multiplier is  not applied to low irradiance days
    """
    # find clear days
    clear_days = (
        out["ac_power"].resample("1D").mean()
        > 0.99 * out["clearsky_ac_power"].resample("1D").mean()
    )
    # find low irradiance days, predicited power is < 50% of clearsky power
    low_irrad_days = (
        out["ac_power"].resample("1D").mean()
        < 0.5 * out["clearsky_ac_power"].resample("1D").mean()
    )
    # find daily std devs
    stds = (out["ac_power"]).groupby(out.index.date).std()
    stds.index = pd.to_datetime(stds.index).tz_localize("utc")
    # take std dev from non-clearsky days only for normalization
    stds = stds.where(~clear_days, other=np.nan)
    # compute a multiplication factor for non-clear times
    #         fixed_max  -  normalized daily standard deviation for non-clear
    #                       days gives variability for remainder of multiplier
    m = 1.0 - 0.5 * (stds - stds.min()) / (stds.max() - stds.min())
    # turn off mulitplier on low irradiance days
    m[low_irrad_days] = 1.0
    return m


def _daytime_limits(period: int, zenith: pd.Series) -> pd.Series:
    res = zenith.resample(f"{period}min")  # type: ignore
    keep: pd.Series = (res.first() <= 90) | (res.last() <= 90)
    # tack on a nighttime period to capture last down ramp after diff
    night = keep.astype(int).diff() == -1  # type: ignore
    keep |= night
    return keep


def _largest_ramps(
    period: int, series: pd.Series, quantile: float, zenith: pd.Series
) -> pd.Series:
    """Find the typical large ramps considering the whole month together"""
    keep_diffs = _daytime_limits(period, zenith)
    out: pd.Series = (
        series.resample(f"{period}min")  # type: ignore
        .mean()
        .diff()[keep_diffs]
        .dropna()
        .groupby(lambda x: x.month)
        .quantile(quantile)
    )
    return out


def _typical_ss_ramps(
    period: int, series: pd.Series, quantile: float, zenith: pd.Series
) -> pd.Series:
    """Apply to a clearsky power to estimate the sunrise/set ramps for each day
    and take the mean over a month for the typical monthly sunrise/set ramp"""
    keep_diffs = _daytime_limits(period, zenith)
    out: pd.Series = (
        series.resample(f"{period}min")  # type: ignore
        .mean()
        .diff()[keep_diffs]
        .dropna()
        .groupby(lambda x: x.date)
        .quantile(quantile)
        .groupby(lambda x: x.month)
        .mean()
    )
    return out


def compute_statistics(system: models.PVSystem, data: pd.DataFrame) -> pd.DataFrame:
    system_center = system.boundary._rect.centroid
    data = data.tz_convert("Etc/GMT+7")  # type: ignore
    zenith = get_solarposition(data.index, system_center.y, system_center.x)["zenith"]
    # remove most of nighttime but keep some to get the diff for morning/evening ramps
    periods = (5, 10, 15, 30, 60)
    out = pd.DataFrame(
        {
            k: v  # type: ignore
            for p in periods
            for k, v in (
                (
                    (f"{p}-min", "p95 daytime ramp"),
                    _largest_ramps(p, data.ac_power, 0.95, zenith),
                ),
                (
                    (f"{p}-min", "p05 daytime ramp"),
                    _largest_ramps(p, data.ac_power, 0.05, zenith),
                ),
                (
                    (f"{p}-min", "worst case ramp up"),
                    _largest_ramps(p, data.ac_power, 0.9999, zenith),
                ),
                (
                    (f"{p}-min", "worst case ramp down"),
                    _largest_ramps(p, data.ac_power, 0.0001, zenith),
                ),
                (
                    (f"{p}-min", "typical sunrise ramp"),
                    _typical_ss_ramps(p, data.clearsky_ac_power, 0.95, zenith),
                ),
                (
                    (f"{p}-min", "typical sunset ramp"),
                    _typical_ss_ramps(p, data.clearsky_ac_power, 0.05, zenith),
                ),
            )
        },
    ).round(2)
    out.index = pd.Index([calendar.month_name[i] for i in out.index], name="month")
    out.columns.names = ["interval", "statistic"]
    return out.melt(ignore_index=False).reset_index()  # type: ignore


def _get_dataset(dataset_name: models.DatasetEnum) -> NSRDBDataset:
    # will take about two seconds to load grid, could possibly preload
    # before the RQ fork, but not worth it for now
    dataset_path = find_dataset_path(dataset_name)
    ds = NSRDBDataset(dataset_path)
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
    try:
        dataset = _get_dataset(dataset_name)
        ac_power = compute_total_system_power(system.definition, dataset)
        stats = compute_statistics(system.definition, ac_power)
    except Exception as err:
        error = {"message": str(err)}
        with si.start_transaction() as st:
            st.update_system_model_data(
                system_id, dataset_name, syshash, None, None, error
            )
        raise

    ac_bytes = utils.dump_arrow_bytes(
        utils.convert_to_arrow(ac_power.reset_index())
    )  # type: ignore
    stats_bytes = utils.dump_arrow_bytes(utils.convert_to_arrow(stats))
    with si.start_transaction() as st:
        st.update_system_model_data(
            system_id, dataset_name, syshash, ac_bytes, stats_bytes
        )
