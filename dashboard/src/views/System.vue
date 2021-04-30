<template>
  <div class="system" v-if="$auth.isAuthenticated">
    <div v-if="system">
      <h2>{{ system.definition.name }}</h2>
      <hr />
      <div class="grid">
        <div class="details">
          <template v-if="system">
            <router-link
              tag="button"
              :to="{
                name: 'Update System',
                params: { systemId: system.object_id },
                query: { returnTo: 'details' },
              }"
              >Update System</router-link
            >
            <button class="delete-system" @click="showDeleteDialog = true">
              Delete System
            </button>
            <ul class="details-list" v-if="system">
              <li><b>Name: </b>{{ system.definition.name }}</li>
              <li>
                <b>AC Capacity (MW): </b>{{ system.definition.ac_capacity }}
              </li>
              <li><b>DC/AC Ratio: </b>{{ system.definition.dc_ac_ratio }}</li>
              <li><b>Albedo: </b>{{ system.definition.albedo }}</li>
              <li>
                <template v-if="'backtracking' in system.definition.tracking">
                  <b>Tracking: </b>
                  <ul class="tracking-details-list">
                    <li>
                      <b>Axis Tilt: </b
                      >{{ system.definition.tracking.axis_tilt }}&deg;
                    </li>
                    <li>
                      <b>Axis Azimuth: </b
                      >{{ system.definition.tracking.axis_azimuth }}&deg;
                    </li>
                    <li>
                      <b>Ground Coverage Ratio: </b
                      >{{ system.definition.tracking.gcr }}
                    </li>
                    <li>
                      <b>Backtracking: </b
                      >{{ system.definition.tracking.backtracking }}
                    </li>
                  </ul>
                </template>
                <template v-else>
                  <b>Panel Orientation: </b>
                  <ul class="tracking-details-list">
                    <li>
                      <b>Tilt: </b>{{ system.definition.tracking.tilt }}&deg;
                    </li>
                    <li>
                      <b>Azimuth: </b
                      >{{ system.definition.tracking.azimuth }}&deg;
                    </li>
                  </ul>
                </template>
              </li>
            </ul>
          </template>
        </div>
        <div>
          <system-map :system="system.definition" :all_systems="otherSystems" />
        </div>
      </div>
      <div>
        <results v-if="system" :system="system" />
      </div>
      <transition name="fade">
        <div v-if="showDeleteDialog" id="delete-dialog">
          <div class="modal-block">
            <p>
              Are you sure you want to delete the system
              {{ system.definition.name }}?
            </p>
            <button class="confirm-deletion" @click="deleteSystem">Yes</button>
            <button class="cancel-deletion" @click="showDeleteDialog = false">
              Cancel
            </button>
          </div>
        </div>
      </transition>
    </div>
    <div v-else>The System could not be found</div>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop } from "vue-property-decorator";
import { StoredPVSystem } from "@/models";

import * as SystemsAPI from "@/api/systems";
import SystemMap from "@/components/Map.vue";
import Results from "@/components/Results.vue";

Vue.component("system-map", SystemMap);
Vue.component("results", Results);

@Component
export default class SystemDetails extends Vue {
  @Prop() systemId!: string;

  systems!: Array<StoredPVSystem>;
  system!: Record<string, any>;
  showDeleteDialog!: boolean;

  created(): void {
    // When the component is created, load the systems list.
    this.loadSystem();
    this.getSystems();
  }

  data(): Record<string, any> {
    return {
      systems: [],
      system: null,
      showDeleteDialog: false,
    };
  }

  async loadSystem(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getSystem(token, this.systemId)
      .then((system: StoredPVSystem) => {
        this.system = system;
      })
      .catch(() => {
        // 404 case, don't set definition
        return;
      });
  }

  async getSystems(): Promise<void> {
    // Load the the list of systems from the api
    const token = await this.$auth.getTokenSilently();
    this.systems = await SystemsAPI.listSystems(token);
  }

  async deleteSystem(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.deleteSystem(token, this.system.object_id)
      .then(() => {
        this.$router.push({ name: "Systems" });
      })
      .catch((error: any) => {
        console.error(error);
        this.showDeleteDialog = false;
      });
  }
  get otherSystems(): Array<StoredPVSystem> {
    return this.systems.filter((system: StoredPVSystem) => {
      return system.object_id != this.systemId;
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
