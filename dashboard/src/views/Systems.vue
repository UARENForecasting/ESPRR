<template>
  <div class="systems" v-if="$auth.isAuthenticated">
    <h2>Systems</h2>
    <hr />
    <div class="grid">
      <div class="systems-table">
        <table v-if="systems.length > 0">
          <thead>
            <tr>
              <th>Name</th>
              <th>AC Capacity</th>
              <th>DC AC Ratio</th>
              <th>Tracking</th>
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
              <td>{{ system.definition.dc_ac_ratio }}</td>
              <td>
                <template v-if="'backtracking' in system.definition.tracking">
                  Single Axis
                </template>
                <template v-else> Fixed </template>
              </td>
            </tr>
          </tbody>
        </table>
        <!-- update with link to system form -->
        <p v-else>No Systems yet. <a href="#">Create a new system.</a></p>
      </div>
      <div class="details">
        <template v-if="systems.length > 0">
          <h3>System Details</h3>
          <!-- Probably create a component to display details and map location-->
          <ul ckass="details-list" v-if="selected">
            <li><b>Name: </b>{{ selected.definition.name }}</li>
            <li><b>AC Capacity: </b>{{ selected.definition.ac_capacity }}</li>
            <li><b>DC AC Ratio: </b>{{ selected.definition.dc_ac_ratio }}</li>
            <li><b>Albedo: </b>{{ selected.definition.albedo }}</li>
            <li>
              <b>Tracking: </b>
              <ul class="tracking-details-list">
                <template v-if="'backtracking' in selected.definition.tracking">
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
                </template>
                <template v-else>
                  <li>
                    <b>Tilt: </b>{{ selected.definition.tracking.tilt }}&deg;
                  </li>
                  <li>
                    <b>Azimuth: </b
                    >{{ selected.definition.tracking.azimuth }}&deg;
                  </li>
                </template>
              </ul>
            </li>
            <li>
              <b>Boundary: </b>
              <ul>
                <li>
                  <b>Northwest Corner: </b>
                  {{ selected.definition.boundary.nw_corner.latitude }} &deg;N,
                  {{ selected.definition.boundary.nw_corner.longitude }} &deg;E
                </li>
                <li>
                  <b>Southeast Corner: </b>
                  {{ selected.definition.boundary.se_corner.latitude }} &deg;N,
                  {{ selected.definition.boundary.se_corner.longitude }} &deg;E
                </li>
              </ul>
            </li>
          </ul>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";
import * as SystemsAPI from "@/api/systems";

@Component
export default class Systems extends Vue {
  systems!: Record<string, any>[];
  selected!: Record<string, any>;

  created(): void {
    // When the component is created, load the systems list.
    this.getSystems();
  }

  data(): Record<string, any> {
    return {
      systems: [],
      selected: null,
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
  setSelected(selectedSystem: Record<string, any>): void {
    this.selected = selectedSystem;
  }
}
</script>
<style>
div.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  grid-template-columns: 1fr 1fr 1fr 1fr;
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
  background-color: #ddd;
}

table {
  border-spacing: 0;
}
</style>
