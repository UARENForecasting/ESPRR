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
// @ts-nocheck
import { PVSystemGroup, StoredPVSystemGroup } from "@/models";
import { Table, FloatVector, DateVector, Builder, Utf8 } from "apache-arrow";
import { systems } from "systems";

let groupIndex = 0;

const timeIndex = [
  (new Date("2021-01-01T00:00Z")).getTime(),
  (new Date("2021-01-02T00:00Z")).getTime(),
  (new Date("2021-01-03T00:00Z")).getTime(),
];

const tsTable = Table.new(
  [
    FloatVector.from(Float32Array.from([1.0, 2.0, 3.0])),
    FloatVector.from(Float32Array.from([1.0, 2.0, 3.0])),
    FloatVector.from(Float32Array.from(timeIndex)),
  ],
  ["ac_power", "clearsky_ac_power", "time"]
);


const monthBuilder = Builder.new({
  type: new Utf8(),
  nullValues: [null]
});
const statBuilder = Builder.new({
  type: new Utf8(),
  nullValues: [null]
});
const intervalBuilder = Builder.new({
  type: new Utf8(),
  nullValues: [null]
});

const stats = ["p95 daytime ramp", "p05 daytime ramp", "typical sunrise ramp", "typical sunset ramp"];
const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

for (const stat of stats) {
  for (const month of months) {
    statBuilder.append(stat);
    monthBuilder.append(month);
    intervalBuilder.append("5-min");
  }
};
const values: Array<number> = [];
for (let i = 0; i < 48; i++) {
  values.push(0.5);
}
const statisticsTable = Table.new(
  [
    monthBuilder.finish().toVector(),
    statBuilder.finish().toVector(),
    intervalBuilder.finish().toVector(),
    FloatVector.from(Float32Array.from(values))
  ],
  ["month", "statistic", "interval", "value"]
);

const groups: Array<StoredPVSystemGroup> = [
  {
    object_id: "04558a7c-c028-11ec-9d64-0242ac120002",
    object_type: "system_group",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Test PV System Group",
      systems: [systems[0]]
    }
  },
  {
    object_id: "2635eb82-c028-11ec-9d64-0242ac120002",
    object_type: "system_grouup",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Real PV System Group",
      systems: systems
    },
  },
];

const listSystemGroups = jest.fn().mockResolvedValue(groups);

const getSystemGroup = jest.fn(async function (
  token: string,
  groupId: string
): Promise<StoredPVSystemGroup> {
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].object_id == groupId) {
      return groups[i];
    }
  }
  throw "Failed to load systems with status code 404";
});

const deleteSystemGroup = jest.fn(async function (
  token: string,
  groupId: string
): Promise<void> {
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].object_id == groupId) {
      groups.splice(i, 1);
      return;
    }
  }
  throw `Could not delete system ${systemId}`;
});

const createSystemGroup = jest.fn(async function (
  token: string,
  definition: PVSystemGroup
): Promise<Record<string, any> | null> {
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].definition.name == definition.name) {
      throw `System Group with name ${definition.name} already exists`;
      return null;
    }
  }
  groups.push({
    object_id: String(groupIndex),
    object_type: "system_group",
    created_at: new Date().toISOString(),
    modified_at: new Date().toISOString(),
    definition: { systems: [], ...definition},
  });
  const response = {
    object_id: String(groupIndex),
  };
  groupIndex++;
  return response;
});
const updateSystemGroup = jest.fn(async function (
  token: string,
  groupId: string,
  definition: PVSystemGroup
): Promise<Record<string, any> | null> {
  let gId: string;
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].object_id == groupId) {
      gId = groups[i].object_id;
      groups[i].definition = definition;
      return {
        object_id: gId,
      };
    }
  }
  return null;
});
const addSystemToSystemGroup = jest.fn(async function (
  token: string,
  groupId: string,
  systemId: string
): Promise<void> {
  for (let i = 0; i < groups.length; i++) {
     let group = groups[i];
     if (group.object_id == groupId) {
       for (let j = 0; j < systems.length; j++){
         let sys = systems[j];
         console.log("comparing ids: \n", sys.object_id, "\n",systemId,"\n");
         if (sys.object_id == systemId) {
           group.definition.systems.push(sys);
           return;
         }
       }
     }
  }
  throw "not found";
});
const removeSystemFromSystemGroup = jest.fn(async function (
  token: string,
  groupId: string,
  systemId: string
): Promise<void> {
  for (let i = 0; i < groups.length; i++) {
     let group = groups[i];
     if (group.object_id == groupID) {
       let groupSystems = group.definition.systems;
       for (let j = 0; j < groupSystems.length; j++){
         let sys = groupSystems[j];
         if (sys.object_id == systemId) {
           groupSystems.splice(j, 1);
           return;
         }
       }
     }
  }
  throw "not found";
});
const getResult = jest.fn(async function (
  token: string,
  groupId: string,
  dataset: string
): Promise<Record<string, any>> {
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].object_id == groupId) {
        let data_status = {};
        for (let system of groups[i].definition.systems) {
          data_status[system.object_id] = {
            system_id: system.object_id,
            status: "complete",
            dataset
          }
        }
        return {
          object_type: "system_group",
          system_data_status: data_status
        }
    }
  }
  throw "not found";
});

const fetchResultTimeseries = jest.fn(async function (
  token: string,
  groupId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  return new Response(new Blob());
});

const getResultTimeseries = jest.fn(async function (
  token: string,
  groupId: string,
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
  groupId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  return new Response(new Blob());
});
const getResultStatistics = jest.fn(async function (
  token: string,
  groupId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Table | string> {
  if (accept == "text/csv") {
    return "stuff";
  } else {
    return statisticsTable;
  }
});

export {
  listSystemGroups,
  getSystemGroup,
  createSystemGroup,
  deleteSystemGroup,
  updateSystemGroup,
  addSystemToSystemGroup,
  removeSystemFromSystemGroup,
  fetchResultTimeseries,
  fetchResultStatistics,
  getResultTimeseries,
  getResultStatistics,
  getResult,
  statisticsTable,
  tsTable,
  groups
};
