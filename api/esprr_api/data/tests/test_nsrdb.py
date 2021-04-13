import geopandas  # type: ignore
import pytest
from shapely import geometry  # type: ignore
from types import GeneratorType
import xarray as xr


from esprr_api import models


def test_open_dataset(dataset):
    with dataset.open_dataset() as ds:
        assert isinstance(ds, xr.Dataset)


def test_load_grid(dataset):
    with pytest.raises(AttributeError):
        dataset.grid
    with pytest.raises(AttributeError):
        dataset.boundary
    dataset.load_grid()
    assert isinstance(dataset.grid, geopandas.GeoSeries)
    assert isinstance(dataset.boundary, geometry.Polygon)


def test_find_system_locations(system_def, ready_dataset):
    # and with smallest bbox possible, pt or lines
    out = ready_dataset.find_system_locations(system_def)
    assert len(out) == 12
    assert abs(sum([pt.fractional_area for pt in out]) - 1) < 1e-6


def test_find_system_locations_outside(system_def, ready_dataset):
    system_def.boundary = models.BoundingBox(
        nw_corner={"latitude": 33.9, "longitude": -117.1},
        se_corner={"latitude": 33.8, "longitude": -117.0},
    )
    with pytest.raises(ValueError):
        ready_dataset.find_system_locations(system_def)


@pytest.mark.parametrize(
    "bbox,num",
    [
        (((32.03, -110.9), (32.03 - 2e-6, -110.9 + 2e-6)), 1),
        (((32.03, -110.9), (32.03 - 2e-6, -110.85)), 3),
        (((32.04, -110.9), (32.01, -110.9 + 2e-6)), 2),
    ],
)
def test_find_system_locations_iter(bbox, system_def, ready_dataset, num):
    system_def.boundary = models.BoundingBox(
        nw_corner={"latitude": bbox[0][0], "longitude": bbox[0][1]},
        se_corner={"latitude": bbox[1][0], "longitude": bbox[1][1]},
    )
    out = ready_dataset.find_system_locations(system_def)
    assert len(out) == num
    assert abs(sum([pt.fractional_area for pt in out]) - 1) < 1e-6


def test_generate_data(system_def, ready_dataset):
    out = ready_dataset.generate_data(system_def)
    assert isinstance(out, GeneratorType)
    ol = list(out)
    assert len(ol) == 12
    assert isinstance(ol[0], models.SystemData)
    assert len(ol[0].weather_data.index) == 17280
