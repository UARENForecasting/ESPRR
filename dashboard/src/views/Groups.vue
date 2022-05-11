<template>
  <div class="groups" v-if="$auth.isAuthenticated">
    <h2>Groups</h2>
    <router-link :to="{ name: 'New Group' }" class="new-group-link btn-spc"
      ><button>Create New Group</button></router-link
    >
    <router-link :to="{ name: 'New DistributedGroup' }" class="new-group-link btn-spc"
      ><button>Create New Distributed Group</button></router-link
    >
    <hr />
    <div class="grid">
      <div class="groups-table">
        <table v-if="groups.length > 0">
          <thead>
            <tr>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-bind:class="{
                'selected-group':
                  selected && group.object_id == selected.object_id,
              }"
              v-for="group of groups"
              :key="group.object_id"
              role="button"
              @click="setSelected(group)"
            >
              <td>{{ group.definition.name }}</td>
            </tr>
          </tbody>
        </table>
        <!-- update with link to system form -->
        <p v-else>
          No System Groups yet.
          <router-link :to="{ name: 'New Group' }" class="new-system-link btn-spc"
            >Create a new Group</router-link
          >
        </p>
      </div>
      <div class="details">
        <template v-if="selected">
          <h3>Group Details</h3>
          <router-link
            class="btn-spc"
            :to="{
              name: 'Group Details',
              params: { groupId: selected.object_id },
              query: { returnTo: 'groups' },
            }"
          >
            <button>Results</button>
          </router-link>
          <router-link
            class="btn-spc"
            :to="{
              name: 'Update Group',
              params: { groupId: selected.object_id },
              query: { returnTo: 'groups' },
            }"
          >
            <button>Update Group</button>
          </router-link>
          <button class="delete-group" @click="showDeleteDialog = true">
            Delete Group
          </button>
          <p>
            <b>Name: </b>{{ selected.definition.name }}<br />
            <template v-if="totalCapacity">
              <b>Total Capacity: </b>{{ totalCapacity }}<br />
            </template>
          </p>
          <b>Systems:</b>
          <div class="group systems-table">
            <table>
              <thead>
                <tr>
                  <th>Plotted Color</th>
                  <th>Name</th>
                  <th>AC Capacity</th>
                  <th>Tracking</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="selected.definition.systems.length == 0">
                  No systems added to group
                </tr>
                <tr
                  v-for="(system, i) of selected.definition.systems"
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
                      Single Axis
                    </template>
                    <template v-else> Fixed Tilt</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <system-map
            :systems="selected.definition.systems"
            @new-selection="setSelected"
          />
        </template>
      </div>
    </div>
    <transition name="fade">
      <div v-if="showDeleteDialog" id="delete-dialog">
        <div class="modal-block">
          <p>
            Are you sure you want to delete the group
            {{ selected.definition.name }}?
          </p>
          <button class="confirm-deletion" @click="deleteGroup">Yes</button>
          <button class="cancel-deletion" @click="showDeleteDialog = false">
            Cancel
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";
import { StoredPVSystemGroup, StoredPVSystem } from "@/models";

import * as GroupsAPI from "@/api/systemGroups";
import SystemMap from "@/components/Map.vue";
import GetColor from "@/utils/Colors";

Vue.component("system-map", SystemMap);

@Component
export default class Groups extends Vue {
  groups!: Array<StoredPVSystemGroup>;
  selected!: Record<string, any> | null;
  showDeleteDialog!: boolean;

  created(): void {
    // When the component is created, load the systems list.
    this.getSystemGroups();
    console.log("groups view created");
  }

  data(): Record<string, any> {
    return {
      groups: [],
      selected: null,
      showDeleteDialog: false,
    };
  }

  async getSystemGroups(): Promise<void> {
    // Load the the list of systems from the api
    const token = await this.$auth.getTokenSilently();
    this.groups = await GroupsAPI.listSystemGroups(token);
    if (this.groups.length) {
      this.setSelected(this.groups[0]);
    } else {
      this.selected = null;
    }
  }
  async deleteGroup(): Promise<void> {
    if (this.selected != null) {
      const token = await this.$auth.getTokenSilently();
      GroupsAPI.deleteSystemGroup(token, this.selected.object_id)
        .then(() => {
          this.getSystemGroups();
          this.showDeleteDialog = false;
        })
        .catch((error: any) => {
          // TODO: display errors to user
          console.error(error);
          this.showDeleteDialog = false;
        });
    }
  }
  async setSelected(selectedSystemGroup: Record<string, any>): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    this.selected = await GroupsAPI.getSystemGroup(
      token,
      selectedSystemGroup.object_id
    );
  }
  get totalCapacity(): number | null {
    if (this.selected) {
      return this.selected.definition.systems
        .map((sys: StoredPVSystem) => sys.definition.ac_capacity)
        .reduce((acc: number, cap: number) => acc + cap, 0);
    } else {
      return null;
    }
  }
  getColor(seed: number): string {
    return GetColor(seed);
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
  border-bottom: 1px solid #ccc;
}
.group.systems-table tr {
  display: grid;
  padding: 0.5em;
  grid-template-columns: 1fr 3fr 1fr 1fr;
  border-bottom: 1px solid #ccc;
}
.group.systems-table tr:hover {
  cursor: auto;
  background: #fff;
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
.new-group-link {
  padding-right: .5em;
}
</style>
