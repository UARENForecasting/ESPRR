<template>
  <div class="group" v-if="$auth.isAuthenticated">
    <div v-if="group">
      <h2>{{ group.definition.name }}</h2>
      <hr />
      <div class="grid">
        <div class="details">
          <template v-if="group">
            <router-link
              :to="{
                name: 'Update Group',
                params: {
                  groupId: group.object_id,
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
            <li>Total Capacity: {{ totalCapacity }}</li>
          </ul>
        </div>
        <div>
          <system-map :systems="systems" />
        </div>
      </div>
      <ul class="result-nav">
        <li><router-link
              :to="{
                name: 'Group Details',
                params: {
                  groupId: group.object_id,
                },
                query: { returnTo: 'details' },
              }"
              ><button>Overview</button></router-link
            ></li>
        <li><router-link
              :to="{
                name: 'Group Dataset Details',
                params: {
                  groupId: group.object_id,
                  dataset: 'NSRDB_2018'
                },
              }"
              ><button>2018</button></router-link
            ></li>
        <li><router-link
              :to="{
                name: 'Group Dataset Details',
                params: {
                  groupId: group.object_id,
                  dataset: 'NSRDB_2019'
                },
              }"
              ><button>2019</button></router-link
            ></li>
        <li><router-link
              :to="{
                name: 'Group Dataset Details',
                params: {
                  groupId: group.object_id,
                  dataset: 'NSRDB_2020'
                },
              }"
              ><button>2020</button></router-link
            ></li>
      </ul>
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
                <template
                  v-if="'backtracking' in system.definition.tracking"
                >
                  {{ system.definition.name }}
                </template>
                <template v-else> Fixed Tilt</template>
              </td>
              <td>
                <template v-if="'NSRDB_2018' in resultStatuses">
                  {{ resultStatuses['NSRDB_2018'][system.object_id].status }}
                </template>
              </td>
              <td>
                <template v-if="'NSRDB_2019' in resultStatuses">
                  {{ resultStatuses['NSRDB_2019'][system.object_id].status }}
                </template>
              </td>
              <td>
                <template v-if="'NSRDB_2020' in resultStatuses">
                  {{ resultStatuses['NSRDB_2020'][system.object_id].status }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div>
      <group-results v-if="group && dataset" :group="group" :dataset="dataset" />
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

  created(): void {
    // When the component is created, load the systems list.
    if (this.dataset) {
      this.datasets = [this.dataset];
    } else {
      this.datasets = validDatasets;
    }
    this.loadGroup();
  }

  data(): Record<string, any> {
    return {
      group: null,
      showDeleteDialog: false,
      resultStatuses: {},
      tableReady: false,
      datasets: []
    };
  }

  async loadGroup(): Promise<void> {
    // fetch system group from api and set definition
    const token = await this.$auth.getTokenSilently();
    GroupsAPI.getSystemGroup(token, this.groupId)
      .then((group: StoredPVSystemGroup) => {
        this.group = group;
        console.log("got group");
        if (typeof this.dataset === "undefined") {
          this.getResultStatuses(token).then(
            ()=> this.tableReady=true
          );
        }
      })
      .catch(() => {
        // 404 case, don't set definition
        return;
      });
  }
  async getSingleResultStatus(token: string, dataset: string): Promise<void>{
    let response: Record<string, any> = {};
    try {
      response = await GroupsAPI.getResult(token, this.groupId, dataset);
    } catch (error: any) {
      return;
    }
    return response.system_data_status;
  }
  async getResultStatuses(token: string): Promise<void> {
    console.log("Inside getResultStatuses");
    let statuses: Record<string, any> = {};
    for (let dataset of this.datasets) {
      statuses[dataset] = await this.getSingleResultStatus(token, dataset);
      for (let system of this.systems) {
        let systemId = system.object_id;
        if (!(systemId in statuses[dataset])){
           statuses[dataset][systemId] = {
             system_modified: false,
             status: "not started"
           }
        }
      }
      this.$set(this.resultStatuses, dataset, statuses[dataset]);
    }
  }
  getColor(seed:number): string {
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
      if (dataset in this.resultStatuses) {
        for (const system in this.resultStatuses[dataset]) {
          resultsReady = resultsReady && this.resultStatuses[dataset][system].status == 'complete';
        }
      } else {
        resultsReady = false;
      }
      grs[dataset] = resultsReady;
    }
    return grs;
  }
  get totalCapacity() {
    if (this.group) {
        return this.group.definition.systems.reduce(
            (acc: number, sys: StoredPVSystem) => acc + sys.definition.ac_capacity,
            0
        );
    } else {
        return null;
    }
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
  padding: .5em;
  background: gray;
}
</style>
