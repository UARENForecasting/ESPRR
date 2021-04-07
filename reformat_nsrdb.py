import dask.array as da
import h5py
import xarray as xr
import zarr

BOUNDARIES = ((31.0, 38.0), (-118.01, -103.01))


def main():
    irradiance_file = h5py.File(
        "/d4/uaren/nsrdb/h5/nsrdb_conus_irradiance_2019.h5", mode="r"
    )
    weather_file = h5py.File("/d4/uaren/nsrdb/h5/nsrdb_conus_pv_2019.h5", mode="r")
    output_path = "/d4/uaren/nsrdb/nsrdb_2019.zarr"

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
    lat = xr.DataArray(coordarr[limits, 0], dims=["spatial_idx"])
    lon = xr.DataArray(coordarr[limits, 1], dims=["spatial_idx"])
    lat.encoding = {"compressor": compressor}
    lon.encoding = {"compressor": compressor}

    data = {}
    for var in ("ghi", "dni", "dhi", "fill_flag"):
        vattr = dict(irradiance_file[var].attrs)
        vattr.pop("scale_factor")
        data[var] = xr.DataArray(
            da.from_array(irradiance_file[var])[:, limits],
            dims=["time_idx", "spatial_idx"],
            attrs={k: str(v) for k, v in vattr.items()},
        ).chunk((times.shape[0]), 96)
        data[var].encoding = {"compressor": compressor}
    for var in ("air_temperature", "wind_speed"):
        vattr = dict(weather_file[var].attrs)
        scale_factor = vattr.pop("scale_factor")
        data[var] = (
            xr.DataArray(
                da.from_array(weather_file[var])[:, limits],
                dims=["time_idx", "spatial_idx"],
                attrs={k: str(v) for k, v in vattr.items()},
            )
            .astype("float32")
            .chunk((times.shape[0], 96))
            / scale_factor
        )
        data[var].encoding = {"compressor": compressor, "scale_factor": scale_factor}
    ds = xr.Dataset(data, coords={"lat": lat, "lon": lon, "times": times})
    ds.to_zarr(output_path, consolidated=True)
    weather_file.close()
    irradiance_file.close()


if __name__ == "__main__":
    main()
