from setuptools import setup, find_packages  # type: ignore


if __name__ == "__main__":
    setup(
        name="esprr-api",
        packages=find_packages(),
        install_requires=[
            "accept-types",
            "cryptography",
            "dask",
            "fastapi",
            "fiona",
            "geopandas",
            "httpx",
            "pandas",
            "prometheus_fastapi_instrumentator",
            "pvlib",
            "pydantic",
            "pygeos",
            "pymysql",
            "python-jose",
            "sentry_sdk",
            "sqlalchemy",
            "requests",
            "pyarrow",
            "redis",
            "rq",
            "xarray",
            "zarr",
        ],
        use_scm_version={
            "write_to": "api/esprr_api/_version.py",
            "root": "api/../..",
        },
        setup_requires=["setuptools_scm"],
        entry_points={"console_scripts": []},
    )
