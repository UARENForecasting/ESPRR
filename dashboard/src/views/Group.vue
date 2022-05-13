<template>
  <div class="group" v-if="$auth.isAuthenticated">
    <div v-if="group">
      <h2>{{ group.definition.name }}</h2>
      <hr />
      <div class="grid">
        <div class="details">
          <template v-if="group">
            <router-link
              class="btn-spc"
              :to="{
                name: 'Update Group',
                params: {
                  groupId: groupId,
                },
                query: { returnTo: 'details' },
              }"
              ><button>Update Group</button></router-link
            >
            <button class="delete-group" @click="showDeleteDialog = true">
              Delete Group
            </button>
          </template>
          <ul>
            <li class="group-capacity">Total Capacity: {{ totalCapacity }}</li>
          </ul>
        </div>
        <div>
          <system-map :systems="systems" />
        </div>
      </div>
      <h2>Systems</h2>
      <div class="group systems-table">
        <table v-if="tableReady">
          <thead>
            <tr>
              <th>Plotted Color</th>
              <th>Name</th>
              <th>AC Capacity</th>
              <th>Tracking</th>
              <th>2018 Status</th>
              <th>2019 Status</th>
              <th>2020 Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="group.definition.systems.length == 0">
              No systems added to group
            </tr>
            <tr
              v-for="(system, i) of group.definition.systems"
              :key="system.object_id"
            >
              <td>
                <span
                  :style="{
                    width: '100%',
                    height: '100%',
                    backgroundColor: getColor(i),
                    fontSize: '20pt',
                  }"
                ></span>
              </td>
              <td>
                {{ system.definition.name }}
              </td>
              <td>
                {{ system.definition.ac_capacity }}
              </td>
              <td>
                <template v-if="'backtracking' in system.definition.tracking">
                  Single Axis
                </template>
                <template v-else> Fixed Tilt</template>
              </td>
              <template v-for="ds in datasets">
                <td :key="ds">
                  <template v-if="ds in resultStatuses">
                    <template
                      v-if="
                        resultStatuses[ds][system.object_id].status ==
                        'complete'
                      "
                    >
                      <button
                        v-if="
                          resultStatuses[ds][system.object_id].system_modified
                        "
                        class="result-link recompute"
                        @click="recompute(system.object_id, ds)"
                      >
                        recompute out of date
                      </button>
                      <router-link
                        v-else
                        :to="{
                          name: 'System Details',
                          params: {
                            systemId: system.object_id,
                            dataset: ds,
                          },
                        }"
                      >
                        <button class="result-link success">
                          {{ resultStatuses[ds][system.object_id].status }}
                        </button>
                      </router-link>
                    </template>
                    <template
                      v-else-if="
                        resultStatuses[ds][system.object_id].status ==
                        'not started'
                      "
                    >
                      <button
                        class="result-link compute"
                        @click="recompute(system.object_id, ds)"
                      >
                        compute
                      </button>
                    </template>
                    <template v-else>
                      {{ resultStatuses[ds][system.object_id].status }}
                    </template>
                  </template>
                </td>
              </template>
            </tr>
            <tr>
              <td></td>
              <td></td>
              <td></td>
              <td></td>
              <td>
                <button
                  v-if="
                    !('NSRDB_2018' in groupResultStatus) ||
                    groupResultStatus['NSRDB_2018'] == 'not started'
                  "
                  @click="queueAll('NSRDB_2018')"
                >
                  Compute 2018
                </button>
                <router-link
                  v-else
                  class="btn-spc"
                  :to="{
                    name: 'Group Dataset Details',
                    params: {
                      groupId: groupId,
                      dataset: 'NSRDB_2018',
                    },
                  }"
                >
                  <button
                    class="group-2018-results"
                    :disabled="
                      !('NSRDB_2018' in groupResultStatus) ||
                      groupResultStatus['NSRDB_2018'] == 'pending'
                    "
                  >
                    2018 Results
                  </button>
                </router-link>
              </td>
              <td>
                <button
                  v-if="
                    !('NSRDB_2019' in groupResultStatus) ||
                    groupResultStatus['NSRDB_2019'] == 'not started'
                  "
                  @click="queueAll('NSRDB_2019')"
                >
                  Compute 2019
                </button>
                <router-link
                  v-else
                  class="btn-spc"
                  :disabled="
                    !('NSRDB_2019' in groupResultStatus) ||
                    groupResultStatus['NSRDB_2019'] == 'pending'
                  "
                  :to="{
                    name: 'Group Dataset Details',
                    params: {
                      groupId: groupId,
                      dataset: 'NSRDB_2019',
                    },
                  }"
                >
                  <button class="group-2019-results">2019 Results</button>
                </router-link>
              </td>
              <td>
                <button
                  v-if="
                    !('NSRDB_2020' in groupResultStatus) ||
                    groupResultStatus['NSRDB_2020'] == 'not started'
                  "
                  @click="queueAll('NSRDB_2020')"
                >
                  Compute 2020
                </button>
                <router-link
                  v-else
                  class="btn-spc"
                  :to="{
                    name: 'Group Dataset Details',
                    params: {
                      groupId: group.object_id,
                      dataset: 'NSRDB_2020',
                    },
                  }"
                >
                  <button
                    class="group-2020-results"
                    :disabled="
                      !('NSRDB_2020' in groupResultStatus) ||
                      groupResultStatus['NSRDB_2020'] == 'pending'
                    "
                  >
                    2020 Results
                  </button>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div>
        <group-results
          v-if="group && dataset"
          :group="group"
          :dataset="dataset"
        />
      </div>
      <transition name="fade">
        <div v-if="showDeleteDialog" id="delete-dialog">
          <div class="modal-block">
            <p>
              Are you sure you want to delete the group
              {{ group.definition.name }}?
            </p>
            <button class="confirm-deletion" @click="deleteGroup">Yes</button>
            <button class="cancel-deletion" @click="showDeleteDialog = false">
              Cancel
            </button>
          </div>
        </div>
      </transition>
    </div>
    <div v-else>The Group could not be found</div>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop } from "vue-property-decorator";
import { StoredPVSystem, StoredPVSystemGroup, validDatasets } from "@/models";

import * as SystemsAPI from "@/api/systems";
import * as GroupsAPI from "@/api/systemGroups";
import SystemMap from "@/components/Map.vue";
import Results from "@/components/GroupResults.vue";
import GetColor from "@/utils/Colors";

Vue.component("system-map", SystemMap);
Vue.component("group-results", Results);

@Component
export default class GroupDetails extends Vue {
  @Prop() groupId!: string;
  @Prop() dataset!: string;

  group!: StoredPVSystemGroup;
  showDeleteDialog!: boolean;
  resultStatuses!: Record<string, any>;
  tableReady!: boolean;
  datasets!: Array<string>;
  timeout!: any;

  created(): void {
    // When the component is created, load the systems list.
    this.datasets = validDatasets;
    this.loadGroup();
  }

  data(): Record<string, any> {
    return {
      group: null,
      showDeleteDialog: false,
      resultStatuses: {},
      tableReady: false,
      datasets: [],
      timeout: null,
    };
  }

  destroyed(): void {
    this.stopPolling();
  }
  async loadGroup(): Promise<void> {
    // fetch system group from api and set definition
    const token = await this.$auth.getTokenSilently();
    GroupsAPI.getSystemGroup(token, this.groupId)
      .then((group: StoredPVSystemGroup) => {
        this.group = group;
        this.getResultStatuses().then(() => (this.tableReady = true));
      })
      .catch(() => {
        // 404 case, don't set definition
        return;
      });
  }
  async getSingleResultStatus(token: string, dataset: string): Promise<any> {
    let response: Record<string, any> = {};
    try {
      response = await GroupsAPI.getResult(token, this.groupId, dataset);
    } catch (error: any) {
      return {};
    }
    return response.system_data_status;
  }
  async getResultStatuses(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    let statuses: Record<string, any> = {};
    for (let dataset of this.datasets) {
      statuses[dataset] = await this.getSingleResultStatus(token, dataset);
      for (let system of this.systems) {
        let systemId = system.object_id;
        if (!(systemId in statuses[dataset])) {
          statuses[dataset][systemId] = {
            system_modified: false,
            status: "not started",
          };
        }
      }
      this.$set(this.resultStatuses, dataset, statuses[dataset]);
      this.stopPolling();
      this.awaitResults();
    }
  }
  getColor(seed: number): string {
    return GetColor(seed);
  }
  get systems(): Array<StoredPVSystem> {
    return this.group.definition.systems ? this.group.definition.systems : [];
  }
  get groupResultStatus(): Record<string, boolean> {
    // result Statuses update asyncronously, check if the dataset has been procesed
    // before accessing the system id
    let grs: Record<string, any> = {};
    for (let dataset of this.datasets) {
      let resultsReady = true;
      let resultsPending = true;
      if (dataset in this.resultStatuses) {
        for (const system in this.resultStatuses[dataset]) {
          resultsReady =
            resultsReady &&
            this.resultStatuses[dataset][system].status == "complete";
          resultsPending =
            resultsPending &&
            !["not started"].includes(
              this.resultStatuses[dataset][system].status
            );
        }
      } else {
        resultsReady = false;
      }
      if (resultsReady) {
        grs[dataset] = "complete";
      } else if (resultsPending) {
        grs[dataset] = "pending";
      } else {
        grs[dataset] = "not started";
      }
    }
    return grs;
  }
  get anyPending(): boolean {
    // result Statuses update asyncronously, check if the dataset has been procesed
    // before accessing the system id
    let isPending = false;
    for (let dataset of this.datasets) {
      if (dataset in this.resultStatuses) {
        for (const system in this.resultStatuses[dataset]) {
          let sysStatus = this.resultStatuses[dataset][system].status;
          isPending =
            isPending || sysStatus == "running" || sysStatus == "queued";
        }
      } else {
        isPending = isPending || false;
      }
    }
    return isPending;
  }
  get totalCapacity(): number | null {
    if (this.group) {
      // @ts-expect-error not actually possibly undefined
      return this.group.definition.systems.reduce(
        (acc: number, sys: StoredPVSystem) => acc + sys.definition.ac_capacity,
        0
      );
    } else {
      return null;
    }
  }
  async stopPolling(): Promise<void> {
    clearTimeout(this.timeout);
    this.timeout = null;
  }
  async awaitResults(): Promise<void> {
    if (this.anyPending) {
      if (this.timeout == null) {
        this.timeout = setTimeout(this.getResultStatuses, 2000);
      }
    } else {
      this.stopPolling();
    }
  }
  async queueAll(dataset: string): Promise<void> {
    for (const system of this.group.definition.systems) {
      const systemId = system.object_id;
      this.recompute(systemId, dataset);
    }
  }
  async recompute(system_id: string, dataset: string): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.startProcessing(token, system_id, dataset).then(() => {
      this.getResultStatuses();
    });
  }
  async deleteGroup(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    GroupsAPI.deleteSystemGroup(token, this.groupId)
      .then(() => {
        this.$router.push({ name: "Groups" });
      })
      .catch((error: any) => {
        console.error(error);
        this.showDeleteDialog = false;
      });
  }
}
</script>
<style scoped>
div.grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
}

.details,
.systems-table {
  display: grid-item;
}

.details {
  padding: 0 1em;
}

table {
  width: 100%;
}

thead tr {
  border-bottom: 1px solid black;
  background-color: white;
}

tbody tr:hover {
  cursor: pointer;
  background: #eee;
}

tr {
  display: grid;
  padding: 0.5em;
  grid-template-columns: 2fr 2fr 1fr;
}

th {
  text-align: left;
}

td:first-child,
th:first-child {
  padding-left: 0;
}

td,
th {
  display: grid;
  padding: 0 1em;
}

tr.selected-site {
  background-color: #ccc;
}

table {
  border-spacing: 0;
}
.new-system-link {
  display: inline-block;
}
#delete-dialog {
  position: fixed;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  display: block;
  background-color: rgba(0, 0, 0, 0.5);
}
#delete-dialog .modal-block {
  width: 500px;
  margin: 35vh auto;
  padding: 2em;
  border: 1px solid #000;
  background-color: #fff;
}
#delete-dialog button {
  display: inline-block;
}
.group.systems-table tr {
  display: grid;
  padding: 0.5em;
  grid-template-columns: 1fr 3fr 1fr 1fr 1fr 1fr 1fr;
  border-bottom: 1px solid #ccc;
}
.group.systems-table tr:hover {
  cursor: auto;
  background: #fff;
}
ul.result-nav {
  display: flex;
  list-style: none;
  flex-direction: row;
  padding-left: 0;
  width: 100%;
}
ul.result-nav li {
  padding: 0.5em;
  background: gray;
}
button.result-link {
  padding: 0.1em 1em;
}
button.result-link:hover {
  cursor: pointer;
}
button.result-link.success:hover {
  background-color: #3eb63e;
}
button.result-link.success {
  color: #fff;
  background-color: #2ea62e;
  border: none;
}
button.result-link.compute:hover {
  background-color: #d44444;
}
button.result-link.compute {
  color: #fff;
  background-color: #c43434;
  border: none;
}
button.result-link.recompute:hover {
  background-color: #eec200;
}
button.result-link.recompute {
  color: #fff;
  background-color: #ccb100;
  border: none;
}
</style>
