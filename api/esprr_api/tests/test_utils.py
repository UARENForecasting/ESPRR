import datetime as dt
from functools import partial
from io import BytesIO


from fastapi import HTTPException
import pandas as pd
import pyarrow as pa
import pytest


from esprr_api import utils


httpfail = partial(
    pytest.param, marks=pytest.mark.xfail(strict=True, raises=HTTPException)
)


@pytest.mark.parametrize(
    "tbl,exp",
    (
        (
            pa.Table.from_arrays([[1.0, 2, 3], [4.0, 5, 6]], ["a", "b"]),
            pd.DataFrame({"a": [1, 2, 3.0], "b": [4, 5, 6.0]}),
        ),
        # complex types to test to_pandas
        (
            pa.Table.from_arrays(
                [pa.array([1.0, 2, 3]), pa.array([[], [5, 6], [7, 8]])], ["a", "b"]
            ),
            pd.DataFrame({"a": [1, 2, 3.0], "b": [[], [5, 6], [7, 8]]}),
        ),
        httpfail(
            b"notanarrowfile",
            None,
        ),
    ),
)
def test_read_arrow(tbl, exp):
    if isinstance(tbl, bytes):
        tblbytes = BytesIO(tbl)
    else:
        tblbytes = BytesIO(utils.dump_arrow_bytes(tbl))
    out = utils.read_arrow(tblbytes)
    pd.testing.assert_frame_equal(out, exp)


@pytest.mark.parametrize(
    "df,tbl",
    (
        (
            pd.DataFrame({"a": [0.1, 0.2]}, dtype="float64"),
            pa.Table.from_arrays(
                [pa.array([0.1, 0.2], type=pa.float32())], names=["a"]
            ),
        ),
        (
            pd.DataFrame({"a": [0.1, 0.2]}, dtype="float32"),
            pa.Table.from_arrays(
                [pa.array([0.1, 0.2], type=pa.float32())], names=["a"]
            ),
        ),
        (
            pd.DataFrame(
                {
                    "a": [0.1, 0.2],
                    "time": [
                        pd.Timestamp("2020-01-01T00:00Z"),
                        pd.Timestamp("2020-01-02T00:00Z"),
                    ],
                },
            ),
            pa.Table.from_arrays(
                [
                    pa.array([0.1, 0.2], type=pa.float32()),
                    pa.array(
                        [
                            dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                            dt.datetime(2020, 1, 2, tzinfo=dt.timezone.utc),
                        ],
                        type=pa.timestamp("s", tz="UTC"),
                    ),
                ],
                names=["a", "time"],
            ),
        ),
        (
            pd.DataFrame(
                {
                    "b": [-999, 129],
                    "time": [
                        pd.Timestamp("2020-01-01T00:00Z"),
                        pd.Timestamp("2020-01-02T00:00Z"),
                    ],
                    "a": [0.1, 0.2],
                },
            ),
            pa.Table.from_arrays(
                [
                    pa.array([-999, 129], type=pa.int64()),
                    pa.array(
                        [
                            dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
                            dt.datetime(2020, 1, 2, tzinfo=dt.timezone.utc),
                        ],
                        type=pa.timestamp("s", tz="UTC"),
                    ),
                    pa.array([0.1, 0.2], type=pa.float32()),
                ],
                names=["b", "time", "a"],
            ),
        ),
        (
            pd.DataFrame(
                {"a": [0.1, 0.2], "time": ["one", "two"]},
            ),
            pa.Table.from_arrays(
                [
                    pa.array([0.1, 0.2], type=pa.float32()),
                    pa.array(["one", "two"]),
                ],
                names=["a", "time"],
            ),
        ),
        # non-localized ok
        (
            pd.DataFrame(
                {
                    "b": [-999, 129],
                    "time": [
                        pd.Timestamp("2020-01-01T00:00"),
                        pd.Timestamp("2020-01-02T00:00"),
                    ],
                    "a": [0.1, 0.2],
                },
            ),
            pa.Table.from_arrays(
                [
                    pa.array([-999, 129], type=pa.int64()),
                    pa.array(
                        [
                            dt.datetime(2020, 1, 1),
                            dt.datetime(2020, 1, 2),
                        ],
                        type=pa.timestamp("s"),
                    ),
                    pa.array([0.1, 0.2], type=pa.float32()),
                ],
                names=["b", "time", "a"],
            ),
        ),
        (
            pd.DataFrame(
                {"nanfloat": [None, 1.0], "nans": [pd.NA, pd.NA], "str": ["a", "b"]}
            ),
            pa.Table.from_arrays(
                [
                    pa.array([None, 1.0], type=pa.float32()),
                    pa.array([None, None], type=pa.null()),
                    pa.array(["a", "b"], type=pa.string()),
                ],
                names=["nanfloat", "nans", "str"],
            ),
        ),
        httpfail(
            pd.DataFrame(
                {
                    "nanint": [pd.NA, 3],  # arrow doesn't like this
                }
            ),
            None,
        ),
        httpfail(
            pd.DataFrame(
                {
                    "nanstr": [pd.NA, "string"],
                }
            ),
            None,
        ),
    ),
)
def test_convert_to_arrow(df, tbl):
    out = utils.convert_to_arrow(df)
    assert out == tbl


@pytest.mark.parametrize(
    "df",
    (
        pd.DataFrame(),
        pd.DataFrame({"a": [0, 1992.9]}),
        pd.DataFrame(
            {
                "b": [-999, 129],
                "time": [
                    pd.Timestamp("2020-01-01T00:00"),
                    pd.Timestamp("2020-01-02T00:00"),
                ],
                "a": [0.1, 0.2],
            },
        ),
        pd.DataFrame(
            {
                "b": [-999, 129],
                "time": [
                    pd.Timestamp("2020-01-01T00:00Z"),
                    pd.Timestamp("2020-01-02T00:00Z"),
                ],
                "a": [0.1, 0.2],
            },
        ),
    ),
)
def test_dump_arrow_bytes(df):
    tbl = pa.Table.from_pandas(df)
    out = utils.dump_arrow_bytes(tbl)
    assert isinstance(out, bytes)
    new = pa.feather.read_feather(BytesIO(out))
    pd.testing.assert_frame_equal(df, new)
