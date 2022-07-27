# ESPRR: Expected Solar Performance and Ramp Rate tool

ESPRR is an interactive web application to model expected power and ramp rates for new
solar PV plants in the Southwest while properly accounting for location, size,
orientation, and geographic diversity. The tool consists of a Vue web frontend backed by
a FastAPI backend to perform the calculations. ESPRR was initially developed with
support from Salt River Project.


## Development Setup

ESPRR has a few dependencies that are required. MySQL and Redis are used for storing
data and queueing jobs respectively. It is easiest to run these in containers to avoid
having to adjust versions on your local system. Node and Python are also required, and
systems for managing Node and Python versions are shown below. It's advisable not to
install ESPRR on your system python installation.

### Non-library dependencies

- Docker (https://docs.docker.com/engine/install/)
  Docker allows us to run containers of MySQL and Redis locally and connect have ESPRR
  connect to them so we do not accidentally alter production data.

- DB Mate (https://github.com/amacneil/dbmate)
  Helps in setting up the MySQL database using migrations. Migrations can be found in
  the `db` directory. Migrations are a sequence of SQL scripts that are applied to
  set up a database. As the system is updated, we can add new migrations to update
  the database as necessary instead of having to start over from scratch.

- Node
  The Javascript runtime that allows us to run the dashboard. It is recommended to use
  NVM (https://github.com/nvm-sh/nvm) to install and manage Node versions. The dashboard
  is known to work on Node v15.8.

- Python
  Some Python interpretter. ESPRR is known to run on 3.9.2. It is recommended to use
  something like Anaconda/Miniconda (https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links)
  or virtualenvs. This documentation will provide examples using conda.

### MySQL and Redis container setup

Docker containers can be run or started using the `esprr_docker_init.sh` script. The script
will create an `esprr-mysql` and `esprr-redis` container and export the `DATABASE_URL` environment
variable required by dbmate. After the first run, these containers will persist on your machine. You
can run the script again to start the containers if they have stopped.
*This script should be run using the command `source esprr_docker_init.sh`
so that it can export the required environment variables.*

### Setting up the MySQL database

The first time you set up MySQL with the script from the previous section, you will need to set
up the database migrations by running the `dbmate up` command from the root of this repository.
This only needs to be done once unless you have deleted and recreated your MySQL containers.


### Python installation and running a dev server

The `api` directory contains the python code for the API. Using conda, you can set up an
environment,install the python dependencies, and run a development server with the commands below.
```
conda create -n esprr python=3.9.2

pip install -r api/requirements.txt

pip install -e api

uvicorn esprr_api.main:app --reload
```

The development server should start on port 8000. You can test that it is working by viewing
the documentation served at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Node installation and running a dev server

The `dashboard` directory contains all of the javascript code for the front end. Using nvm,
you can install and run a development server with the commands below.

```
nvm install 15.8

nvm use 15.8

# make sure you're in the dashboard directory
cd dashboard

npm install .

npm run serve -- --port 8080
```

The development server should be available at (http://127.0.0.1:8080)[http://127.0.0.1:8080]

### Running a worker

A Redis Queue worker can be run from a python environment with the ERPRR API dependencies installed.
Use the command `rq worker jobs --with-scheduler` to start a worker. Note that the worker will be
unable to produce data until it has access to the NSRDB data discussed in the "Background Dataset"
section.

## Background Dataset

ESPRR uses the [NSRDB](https://nsrdb.nrel.gov/) dataset to produce modeled plant output. The `reformat_nsrdb.py`
script is used to subset the raw data files to an area covering Arizona and convert them to the .zarr format. The
script can be modified to output smaller files, but the raw NSRDB files are required as input and are
approximately 2 TB in size each.

The rq workers should be pointed to a directory containing your processed `.zarr` files by setting the
`ESPRR_NSRDB_DATA_PATH` environment variable to the path of the appropriate `.zarr` file.

*NOTE* A very small subset of NSRDB data with information around lat, lon 32.03, -110.9 can be found
in the `api/esprr_api/data` directory. It can be decompressed using the command `tar -xvf nsrdb.zarr.tar`.
The appropriate environment variable can then be set with `export ESPRR_NSRDB_DATA_PATH="<repo_path>/esprr_api/data/nsrdb.zarr`.
This data is really only helpful in testing that the platform is functioning and will fail for sites
not at the previously mentioned latitude and longitude.
