import logging
from typing import IO, Type, Union, Optional, Tuple


from accept_types import AcceptableType  # type: ignore
from fastapi import HTTPException, Response
import pandas as pd
import pandas.api.types as pdtypes  # type: ignore
import pyarrow as pa  # type: ignore


logger = logging.getLogger(__name__)


def read_arrow(content: IO) -> pd.DataFrame:
    """Read a buffer in Apache Arrow File format into a DataFrame"""
    try:
        table = pa.ipc.open_file(content).read_all()
    except pa.lib.ArrowInvalid as err:
        raise HTTPException(status_code=400, detail=err.args[0])
    df: pd.DataFrame = table.to_pandas(split_blocks=True)
    return df


def _map_pandas_val_to_arrow_dtypes(ser: pd.Series) -> pa.DataType:
    # save on storage w/ second precisison timestamps and float32
    dtype = ser.dtype  # type: ignore
    if pdtypes.is_datetime64_any_dtype(dtype):
        return pa.timestamp("s", tz=getattr(dtype, "tz", None))
    elif pdtypes.is_float_dtype(dtype):
        return pa.float32()
    else:
        return pa.array(ser, from_pandas=True).type


def convert_to_arrow(df: pd.DataFrame) -> pa.Table:
    """Convert a DataFrame into an Arrow Table setting datetime columns to
    have second precision, float columns to be float32, and infer other types.
    Errors are likely if the first row of a column is NA and the column isn't a
    float.
    """
    try:
        schema = pa.schema(
            (col, _map_pandas_val_to_arrow_dtypes(val))
            for col, val in df.iloc[:1].items()  # type: ignore
        )
        table = pa.Table.from_pandas(df, schema=schema)
    except pa.lib.ArrowInvalid as err:
        logger.error(err.args[0])
        raise HTTPException(status_code=400, detail=err.args[0])
    return table


def dump_arrow_bytes(table: pa.Table) -> bytes:
    """Dump an Arrow table out to bytes in the Arrow File/Feather format"""
    sink = pa.BufferOutputStream()
    writer = pa.ipc.new_file(sink, table.schema)
    writer.write(table)
    writer.close()
    out: bytes = sink.getvalue().to_pybytes()
    return out


class ArrowResponse(Response):
    media_type = "application/vnd.apache.arrow.file"


class CSVResponse(Response):
    media_type = "text/csv"


def _get_return_type(
    accept: Optional[str],
) -> Tuple[Union[Type[CSVResponse], Type[ArrowResponse]], str]:
    if accept is None:
        accept = "*/*"
    type_ = AcceptableType(accept)

    if type_.matches("text/csv"):
        return CSVResponse, "text/csv"
    elif type_.matches("application/vnd.apache.arrow.file"):
        return ArrowResponse, "application/vnd.apache.arrow.file"
    else:
        raise HTTPException(
            status_code=406,
            detail="Only 'text/csv' or 'application/vnd.apache.arrow.file' acceptable",
        )
