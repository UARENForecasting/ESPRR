from pathlib import Path


import dask.array as da
import h5py
import numpy as np
import pandas as pd
import xarray as xr
import zarr


# restrict data to this lat, lon range
# nsrdb had no data over the ocean, so not a regular grid
BOUNDARIES = ((31.0, 38.0), (-118.01, -103.01))


def load_file(fname):
    data = np.fromfile(fname, ">i2", 3601 * 3601).reshape((3601, 3601))
    lat = int(fname.split("/")[-1][1:3])
    lon = int(fname.split("/")[-1][4:7]) * -1
    # Files are named like N32W110 which span from 32 to 33N and -110 to -109 W
    da = (
        xr.DataArray(
            data,
            dims=["lat", "lon"],
            coords=[np.linspace(lat + 1, lat, 3601), np.linspace(lon, lon + 1, 3601)],
        )
        .to_dataset(name="elevation")
        .isel(
            lat=slice(None, None, 72), lon=slice(36, None, 72)
        )  # only keep points at nsrdb grid
    )
    return da


def load_elevation_ds():
    srtm_dir = Path(
        "/d4/uaren/srtm1/"
    )  # files downloaded from AWS s3://elevation-tiles-prod/skadi
    elevations = None
    for f in srtm_dir.glob("*.hgt"):
        da = load_file(str(f))
        if elevations is None:
            elevations = da
        else:
            elevations = elevations.combine_first(da)
    return elevations


def main():
    # files from AWS s3://nrel-pds-nsrdb/conus/ ~2TB each
    base = Path("/d4/uaren/nsrdb")
    irradiance_file = h5py.File(
        base / "h5" / "nsrdb_conus_irradiance_2019.h5", mode="r"
    )
    weather_file = h5py.File(base / "h5" / "nsrdb_conus_pv_2019.h5", mode="r")
    clr_file = h5py.File(base / "h5" / "nsrdb_conus_clearsky_2019.h5", mode="r")
    output_path = base / "nsrdb_2019.zarr"

    # find coordidnate limits
    coords = irradiance_file["coordinates"][:]
    limits = (
        (coords[:, 0] >= BOUNDARIES[0][0])
        & (coords[:, 0] <= BOUNDARIES[0][1])
        & (coords[:, 1] >= BOUNDARIES[1][0])
        & (coords[:, 1] <= BOUNDARIES[1][1])
    )

    # put the data into an xarray dataset
    compressor = zarr.Blosc(cname="zstd", clevel=3, shuffle=2)

    times = xr.DataArray(
        irradiance_file["time_index"][:].astype("datetime64[s]"), dims=["time_idx"]
    )
    times.encoding = {"compressor": compressor}

    coordarr = da.from_array(irradiance_file["coordinates"])
    lat = xr.DataArray(coordarr[limits, 0], dims=["spatial_idx"]).compute()
    lon = xr.DataArray(coordarr[limits, 1], dims=["spatial_idx"]).compute()
    lat.encoding = {"compressor": compressor}
    lon.encoding = {"compressor": compressor}

    # get elevations
    elevation_ds = load_elevation_ds()
    lat_lon_df = pd.DataFrame({"lat": lat, "lon": lon})
    elev_df = lat_lon_df.apply(
        lambda x: elevation_ds.elevation.sel(
            lon=x.lon, lat=x.lat, method="nearest"
        ).item(),
        axis=1,
    )
    elev_df[elev_df < 0] = 0
    elevation_da = xr.DataArray(elev_df.astype("uint16").values, dims=["spatial_idx"])
    elevation_da.encoding = {"compressor": compressor}

    data = {}
    vars_ = (
        [(v, irradiance_file) for v in ("ghi", "dni", "dhi", "fill_flag")]
        + [(v, weather_file) for v in ("air_temperature", "wind_speed")]
        + [(f"clearsky_{v}", clr_file) for v in ("ghi", "dni", "dhi")]
    )
    for var, f in vars_:
        encoding_dict = {"compressor": compressor}
        vattr = dict(f[var].attrs)
        scale_factor = vattr.pop("scale_factor")
        arr = da.from_array(f[var])[:, limits]
        if scale_factor != 1.0:
            arr = arr.astype("float32") / scale_factor
            encoding_dict["scale_factor"] = scale_factor
        data[var] = xr.DataArray(
            arr,
            dims=["time_idx", "spatial_idx"],
            attrs={k: str(v) for k, v in vattr.items()},
        ).chunk((times.shape[0], 96))
        data[var].encoding = encoding_dict
    ds = xr.Dataset(
        data, coords={"lat": lat, "lon": lon, "elevation": elevation_da, "times": times}
    )
    ds.to_zarr(output_path, consolidated=True)
    weather_file.close()
    irradiance_file.close()


if __name__ == "__main__":
    main()
