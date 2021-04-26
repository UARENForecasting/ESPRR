<template>
  <div class="systems" v-if="$auth.isAuthenticated">
    <h2>Systems</h2>
    <router-link :to="{ name: 'New System' }" class="new-system-link"
      >Create New System</router-link
    >
    <hr />
    <div class="grid">
      <div class="systems-table">
        <table v-if="systems.length > 0">
          <thead>
            <tr>
              <th>Name</th>
              <th>AC Capacity (MW)</th>
              <th>Orientation/Tracking</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-bind:class="{
                'selected-site':
                  selected && system.object_id == selected.object_id,
              }"
              v-for="system of systems"
              :key="system.object_id"
              role="button"
              @click="setSelected(system)"
            >
              <td>{{ system.definition.name }}</td>
              <td>{{ system.definition.ac_capacity }}</td>
              <td>
                <template v-if="'backtracking' in system.definition.tracking">
                  Single Axis
                </template>
                <template v-else> Fixed Tilt</template>
              </td>
            </tr>
          </tbody>
        </table>
        <!-- update with link to system form -->
        <p v-else>No Systems yet. <a href="#">Create a new system.</a></p>
      </div>
      <div class="details">
        <template v-if="selected">
          <h3>System Details</h3>
          <router-link
            tag="button"
            :to="{
              name: 'Update System',
              params: { systemId: selected.object_id },
            }"
            >Update System</router-link
          >
          <button class="delete-system" @click="showDeleteDialog = true">
            Delete System
          </button>
          <ul ckass="details-list" v-if="selected">
            <li><b>Name: </b>{{ selected.definition.name }}</li>
            <li>
              <b>AC Capacity (MW): </b>{{ selected.definition.ac_capacity }}
            </li>
            <li><b>DC/AC Ratio: </b>{{ selected.definition.dc_ac_ratio }}</li>
            <li><b>Albedo: </b>{{ selected.definition.albedo }}</li>
            <li>
              <template v-if="'backtracking' in selected.definition.tracking">
                <b>Tracking: </b>
                <ul class="tracking-details-list">
                  <li>
                    <b>Axis Tilt: </b
                    >{{ selected.definition.tracking.axis_tilt }}&deg;
                  </li>
                  <li>
                    <b>Axis Azimuth: </b
                    >{{ selected.definition.tracking.axis_azimuth }}&deg;
                  </li>
                  <li>
                    <b>Ground Coverage Ratio: </b
                    >{{ selected.definition.tracking.gcr }}
                  </li>
                  <li>
                    <b>Backtracking: </b
                    >{{ selected.definition.tracking.backtracking }}
                  </li>
                </ul>
              </template>
              <template v-else>
                <b>Panel Orientation: </b>
                <ul class="tracking-details-list">
                  <li>
                    <b>Tilt: </b>{{ selected.definition.tracking.tilt }}&deg;
                  </li>
                  <li>
                    <b>Azimuth: </b
                    >{{ selected.definition.tracking.azimuth }}&deg;
                  </li>
                </ul>
              </template>
            </li>
          </ul>
          <system-map
            :system="selected.definition"
            :all_systems="notSelectedSystems"
            @new-selection="setSelected"
          />
          
        </template>
      </div>
    </div>
    <div>
        <results
            v-if="selected"
            :systemId="selected.object_id"
          />
    </div>
    <transition name="fade">
      <div v-if="showDeleteDialog" id="delete-dialog">
        <div class="modal-block">
          <p>
            Are you sure you want to delete the system
            {{ selected.definition.name }}?
          </p>
          <button class="confirm-deletion" @click="deleteSystem">Yes</button>
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
import { StoredPVSystem } from "@/models";

import * as SystemsAPI from "@/api/systems";
import SystemMap from "@/components/Map.vue";
import Results from "@/components/Results.vue";

Vue.component("system-map", SystemMap);
Vue.component("results", Results);

@Component
export default class Systems extends Vue {
  systems!: Array<StoredPVSystem>;
  selected!: Record<string, any>;
  showDeleteDialog!: boolean;

  created(): void {
    // When the component is created, load the systems list.
    this.getSystems();
  }

  data(): Record<string, any> {
    return {
      systems: [],
      selected: null,
      showDeleteDialog: false,
    };
  }

  async getSystems(): Promise<void> {
    // Load the the list of systems from the api
    const token = await this.$auth.getTokenSilently();
    this.systems = await SystemsAPI.listSystems(token);

    if (this.systems.length) {
      this.setSelected(this.systems[0]);
    }
  }
  async deleteSystem(): Promise<void> {
    if (this.selected != null) {
      const token = await this.$auth.getTokenSilently();
      SystemsAPI.deleteSystem(token, this.selected.object_id)
        .then(() => {
          this.getSystems();
          this.showDeleteDialog = false;
        })
        .catch((error: any) => {
          // TODO: display errors to user
          console.error(error);
          this.showDeleteDialog = false;
        });
    }
  }
  setSelected(selectedSystem: Record<string, any>): void {
    this.selected = selectedSystem;
  }
  get notSelectedSystems(): Array<StoredPVSystem> {
    return this.systems.filter((system: StoredPVSystem) => {
      return system.object_id != this.selected.object_id;
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
</style>
