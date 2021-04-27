/* Provides default mock values for systems api module.
 * Each exported function is mocked with a jest.fn.
 *
 * Use by calling jest.mock("@/api/systems") in test.
 *
 * Results may be mocked by importing the original function
 * e.g. import { listSystems } from "@/api/systems"
 * and calling listSystems.mockResolvedValues.
 */
/* eslint-disable */
import { PVSystem, StoredPVSystem } from "@/models";
import { Table, FloatVector, DateVector } from "apache-arrow";

let systemIndex = 0;

const timeIndex = [
  new Date("2021-01-01T00:00Z"),
  new Date("2021-01-02T00:00Z"),
  new Date("2021-01-03T00:00Z"),
];

const tsTable = Table.new(
  [
    FloatVector.from(Float32Array.from([1.0, 2.0, 3.0])),
    FloatVector.from(Float32Array.from([1.0, 2.0, 3.0])),
    DateVector.from(timeIndex),
  ],
  ["ac_power", "clearsky_ac_power", "time"]
);
const systems: Array<StoredPVSystem> = [
  {
    object_id: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
    object_type: "system",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Test PV System",
      boundary: {
        nw_corner: {
          latitude: 34.9,
          longitude: -112.9,
        },
        se_corner: {
          latitude: 33,
          longitude: -111,
        },
      },
      ac_capacity: 10,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: {
        tilt: 20,
        azimuth: 180,
      },
    },
  },
  {
    object_id: "6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9",
    object_type: "system",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Real PV System",
      boundary: {
        nw_corner: {
          latitude: 34.9,
          longitude: -112.9,
        },
        se_corner: {
          latitude: 33,
          longitude: -111,
        },
      },
      ac_capacity: 10,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: {
        axis_tilt: 20,
        axis_azimuth: 180,
        gcr: 0.5,
        backtracking: false,
      },
    },
  },
];

const listSystems = jest.fn().mockResolvedValue(systems);

const getSystem = jest.fn(async function (
  token: string,
  systemId: string
): Promise<StoredPVSystem> {
  for (let i = 0; i < systems.length; i++) {
    if (systems[i].object_id == systemId) {
      return systems[i];
    }
  }
  throw "Failed to load systems with status code 404";
});

const deleteSystem = jest.fn(async function (
  token: string,
  systemId: string
): Promise<void> {
  for (let i = 0; i < systems.length; i++) {
    if (systems[i].object_id == systemId) {
      systems.splice(i, 1);
      return;
    }
  }
  throw `Could not delete system ${systemId}`;
});

const createSystem = jest.fn(async function (
  token: string,
  definition: PVSystem
): Promise<Record<string, any> | null> {
  for (let i = 0; i < systems.length; i++) {
    if (systems[i].definition.name == definition.name) {
      throw `Site with name ${definition.name} already exists`;
      return null;
    }
  }
  systems.push({
    object_id: String(systemIndex),
    object_type: "system",
    created_at: new Date().toISOString(),
    modified_at: new Date().toISOString(),
    definition: definition,
  });
  const response = {
    object_id: String(systemIndex),
  };
  systemIndex++;
  return response;
});
const updateSystem = jest.fn(async function (
  token: string,
  systemId: string,
  definition: PVSystem
): Promise<Record<string, any> | null> {
  let sysId: string;
  for (let i = 0; i < systems.length; i++) {
    if (systems[i].object_id == systemId) {
      sysId = systems[i].object_id;
      systems[i].definition = definition;
      return {
        object_id: sysId,
      };
    }
  }
  return null;
});

const startProcessing = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string
): Promise<Record<string, any>> {
  return { result: "ok" };
});
const getResult = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string
): Promise<Record<string, any>> {
  return { status: "complete" };
});

const fetchResultTimeseries = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  return new Response(new Blob());
});

const getResultTimeseries = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Table | string> {
  if (accept == "text/csv") {
    return "stuff";
  } else {
    return tsTable;
  }
});

const fetchResultStatistics = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  return new Response();
});
const getResultStatistics = jest.fn(async function (
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Table | string> {
  if (accept == "text/csv") {
    return "stuff";
  } else {
    return tsTable;
  }
});

export {
  listSystems,
  getSystem,
  createSystem,
  deleteSystem,
  updateSystem,
  startProcessing,
  fetchResultTimeseries,
  fetchResultStatistics,
  getResultTimeseries,
  getResultStatistics,
  getResult,
};
