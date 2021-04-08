from contextlib import contextmanager
from pathlib import Path
from typing import ContextManager, Optional, List, NamedTuple


import geopandas  # type: ignore
from shapely import geometry
import xarray as xr


from .. import models


CRS = (
    "+proj=lcc +lat_1=31 +lat_2=38 +lon_0=-110.5 +x_0=0 +y_0=0 "
    "+ellps=WGS84 +datum=WGS84 +units=km no_defs"
)


class SpatialIndexPoint(NamedTuple):
    spatial_idx: int
    fractional_area: float


class NSRDBDataset:
    pt_buffer = 0.01

    def __init__(self, data_path: Path) -> None:
        self.data_path: Path = data_path
        self._dataset: Optional[xr.Dataset] = None
        self._grid: Optional[geopandas.GeoSeries] = None

    @property
    def dataset(self) -> xr.Dataset:
        if self._dataset is None:
            raise AttributeError("Dataset is only available within `open_dataset`")
        return self._dataset

    def open_dataset(self) -> ContextManager[xr.Dataset]:
        # mypy workaround
        @contextmanager
        def opener():
            with xr.open_zarr(self.data_path, mode="r") as ds:
                self._dataset = ds
                yield ds
            self._dataset = None

        return opener()

    def load_grid(self) -> None:
        with self.open_dataset() as ds:
            lats = ds.lat.values
            lons = ds.lon.values
            index = ds.spatial_idx.values
        pts = geopandas.points_from_xy(lons, lats)
        self._grid = geopandas.GeoSeries(pts, index=index, crs="EPSG:4326")
        self._grid.sindex  # load the index tree

    @property
    def grid(self) -> geopandas.GeoSeries:
        if self._grid is None:
            raise AttributeError("Grid only available after `load_grid` call")
        return self._grid.copy()  # don't want any accidental modifications

    def find_system_locations(
        self, pvsystem: models.PVSystem
    ) -> List[SpatialIndexPoint]:
        boundary = pvsystem.boundary
        # make a shapely polygon for the system
        system_rect = geometry.box(
            minx=boundary.nw_corner.longitude,
            miny=boundary.se_corner.latitude,
            maxx=boundary.se_corner.longitude,
            maxy=boundary.nw_corner.latitude,
        )
        # find the nsrdb grid points in/near the system
        # quicker than only finding the intersection on the entire grid
        possible_points = self.grid.sindex.query(system_rect.buffer(self.pt_buffer))
        # make polygons representing each grid point in/near the system
        # resolution=1 uses one segement per qtr circle, so makes a rectangle
        possible_grid_boxes = (
            (self.grid.iloc[possible_points])
            .buffer(self.pt_buffer, resolution=1)
            .envelope
        )

        # now take intersection of system rect and grid boxes
        # has effect of cutting grid boxes overlapping edge of system rect
        intersecting_grid_boxes = possible_grid_boxes.insersection(rect)

        # find the area of each grid box in the km^2 using appropriate projection
        area_ser = intersecting_grid_boxes.to_crs(CRS).area
        area_ser /= area_ser.sum()

        points = [
            SpatialIndexPoint(spatial_idx=ind, fractional_area=area)
            for ind, area in area_ser.items()
        ]
        return points
