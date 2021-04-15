from contextlib import contextmanager
from pathlib import Path
from typing import ContextManager, Optional, List, NamedTuple, Generator
import warnings


import geopandas  # type: ignore
from shapely import geometry  # type: ignore
import xarray as xr


from .. import models, settings


CRS = (
    "+proj=lcc +lat_1=31 +lat_2=38 +lon_0=-110.5 +x_0=0 +y_0=0 "
    "+ellps=WGS84 +datum=WGS84 +units=km no_defs"
)


class SpatialIndexPoint(NamedTuple):
    spatial_idx: int
    fractional_area: float


class NSRDBDataset:
    """Irradiance and weather data from NSRDB on a roughly 2km grid and 5 minute
    resolution"""

    pt_buffer = 0.01

    def __init__(self, data_path: Optional[Path] = None) -> None:
        self.data_path: Path = (
            data_path if data_path is not None else settings.nsrdb_data_path
        )
        self._grid: Optional[geopandas.GeoSeries] = None
        self._boundary: Optional[geometry.Polygon] = None

    def open_dataset(self) -> ContextManager[xr.Dataset]:
        """Contextmanager to open the zarr dataset"""
        # mypy workaround
        @contextmanager
        def opener():
            with xr.open_zarr(self.data_path) as ds:
                yield ds

        return opener()

    def load_grid(self) -> None:
        """Load the NSRDB lat/lon grid into a geopandas.GeoSeries"""
        with self.open_dataset() as ds:
            lats = ds.lat.values
            lons = ds.lon.values
            index = ds.spatial_idx.values
        pts = geopandas.points_from_xy(lons, lats)
        self._grid = geopandas.GeoSeries(pts, index=index, crs="EPSG:4326")
        self._grid.sindex.query(geometry.Point(-110.1, 32.2))  # load the index tree
        self._boundary = self._grid.unary_union.convex_hull.buffer(
            self.pt_buffer + 1e-4  # extend a bit past outer box
        )

    @property
    def grid(self) -> geopandas.GeoSeries:
        if self._grid is None:
            raise AttributeError("Grid only available after `load_grid` call")
        return self._grid

    @property
    def boundary(self) -> geometry.Polygon:
        if self._boundary is None:
            raise AttributeError("Boundary only available after `load_grid` call")
        return self._boundary

    def find_system_locations(
        self, pvsystem: models.PVSystem
    ) -> List[SpatialIndexPoint]:
        """Find the spatial index and fractiona area of the intersection of the NSRDB and the
        bounding box of the system
        """
        sys_boundary = pvsystem.boundary
        # make a shapely polygon for the system
        system_rect = geometry.box(
            minx=sys_boundary.nw_corner.longitude,
            miny=sys_boundary.se_corner.latitude,
            maxx=sys_boundary.se_corner.longitude,
            maxy=sys_boundary.nw_corner.latitude,
        )
        # first check that the system is within the boundary of the grid
        if not system_rect.within(self.boundary):
            raise ValueError("System is outside the boundary of the background dataset")

        # find the nsrdb grid points in/near the system
        # quicker than only finding the intersection on the entire grid
        possible_points = self.grid.sindex.query(system_rect.buffer(self.pt_buffer))
        # make polygons representing each grid point in/near the system
        # resolution=1 uses one segement per qtr circle, so makes a rectangle
        with warnings.catch_warnings():  # ignore buffer warnings
            warnings.simplefilter("ignore", category=UserWarning)
            possible_grid_boxes = (
                (self.grid.iloc[possible_points])
                .buffer(self.pt_buffer, resolution=1)
                .envelope
            )

        # now take intersection of system rect and grid boxes
        # has effect of cutting grid boxes overlapping edge of system rect
        intersecting_grid_boxes = possible_grid_boxes.intersection(system_rect)

        # find the area of each grid box in the km^2 using appropriate projection
        area_ser = intersecting_grid_boxes.to_crs(CRS).area.sort_index()
        # drop points that have insignificant areas
        area_ser = area_ser[area_ser > area_ser.max() / 1000]
        # find fractional area
        area_ser /= area_ser.sum()

        points = [
            SpatialIndexPoint(spatial_idx=ind, fractional_area=area)
            for ind, area in area_ser.items()
        ]
        return points

    def generate_data(
        self, pvsystem: models.PVSystem
    ) -> Generator[models.SystemData, None, None]:
        """
        Generator that produces models.SystemData objects holding the location, fraction
        of total, and weather data for each location that should be modeled.
        """
        points = self.find_system_locations(pvsystem)
        cols = ["ghi", "dni", "dhi", "wind_speed", "air_temperature"]
        with self.open_dataset() as ds:
            for pt in points:
                data = ds[cols].sel(spatial_idx=pt.spatial_idx).compute()
                loc = models.Location(
                    latitude=data.lat.item(),
                    longitude=data.lon.item(),
                    altitude=data.elevation.item(),
                )
                weather_df = (
                    data.to_dataframe()  # type: ignore
                    .set_index("times")
                    .tz_localize("UTC")[cols]
                    .rename(columns={"air_temperature": "temp_air"})
                    .astype("float32")
                )
                sysd = models.SystemData(
                    location=loc,
                    fraction_of_total=pt.fractional_area,
                    weather_data=weather_df,
                )
                yield sysd