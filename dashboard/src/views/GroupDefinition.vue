<template>
  <div class="system-definition-form">
    <h2 v-if="groupId">Update System Group</h2>
    <h2 v-else>Create New System Group</h2>
    <hr />
    <div v-if="definition" class="definition-container">
      <div id="definition-inputs">
        <ul class="error-list" v-if="errors">
          <li v-for="(field, error) in errors" :key="error">
            <b>{{ error }}:</b> {{ errors[error] }}
          </li>
        </ul>
        <form
          v-if="definition"
          id="group-definition"
          @submit="submitSystemGroup"
        >
          <label
            title="A name for this system group. Most special characters beyond space, comma, hyphen, and parentheses are not allowed."
            >Name:
            <input
              type="text"
              maxlength="128"
              size="24"
              required
              pattern="^(?!\W+$)(?![_ ',\-\(\)]+$)[\w ',\-\(\)]*$"
              v-model="definition.name"
          /></label>
          <h2>Systems:</h2>
          <div class="systems-table">
            <table v-if="this.systems">
              <thead>
                <tr>
                  <th>Included in group</th>
                  <th>Name</th>
                  <th>AC Capacity</th>
                  <th>Tracking</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="this.systems.length == 0">
                  No systems defined
                </tr>
                <tr v-for="system of this.systems" :key="system.object_id">
                  <td>
                    <input
                      type="checkbox"
                      :value="system.object_id"
                      v-model="selectedSystems"
                    />
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
                </tr>
              </tbody>
            </table>
          </div>
          <button type="submit">
            <template v-if="groupId">Update</template
            ><template v-else>Create</template> System Group
          </button>
        </form>
      </div>
    </div>
    <div v-else>The System Group could not be found.</div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop } from "vue-property-decorator";
import * as SystemsAPI from "@/api/systems";
import * as GroupsAPI from "@/api/systemGroups";
import flattenErrors from "@/api/errors";
import SystemMap from "@/components/Map.vue";
import SurfaceTypes from "@/constants/surface_albedo.json";

import { StoredPVSystem, StoredPVSystemGroup, PVSystemGroup } from "@/models";

Vue.component("system-map", SystemMap);

@Component
export default class SystemDefinition extends Vue {
  @Prop() groupId!: string;

  definition!: PVSystemGroup;
  trackingType!: string;
  systems!: Array<StoredPVSystem>;
  selectedSystems!: Array<string>;
  errors!: Record<string, string> | null;
  surfaceTypes: Record<string, number> = SurfaceTypes;
  results!: Record<any, any>;

  data(): Record<string, any> {
    return {
      definition: this.definition,
      trackingType: this.trackingType,
      systems: null,
      errors: null,
      selectedSystems: [],
    };
  }

  created(): void {
    if (this.groupId) {
      this.loadGroup();
      this.loadSystems();
    } else {
      this.definition = {
        name: "New System Group",
        systems: [],
      };
      this.loadSystems();
    }
  }

  async loadGroup(): Promise<void> {
    // fetch system group from api and set definition
    const token = await this.$auth.getTokenSilently();
    GroupsAPI.getSystemGroup(token, this.groupId)
      .then((group: StoredPVSystemGroup) => {
        this.definition = group.definition;
        this.setSelectedSystems();
        GroupsAPI.getResult(token, this.groupId, "NSRDB_2019").then(
          (result: any) => (this.results = result)
        );
      })
      .catch(() => {
        // 404 case, don't set definition
        return;
      });
  }

  async loadSystems(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.listSystems(token)
      .then((systems: Array<StoredPVSystem>) => {
        this.systems = systems;
      })
      .catch((errors: any) => {
        // List systems should not fail under normal circumstances.
        // log the error so it can be debugged in production and
        // prompt user to retry.
        console.error(errors);
        this.errors = {
          Error: "Failed to load systems. Refresh the page to try again.",
        };
      });
  }

  navigateToPrevious(): void {
    this.$router.push({ name: "Groups" });
  }

  async submitSystemGroup(e: Event): Promise<void> {
    e.preventDefault();
    // validate and post system
    const token = await this.$auth.getTokenSilently();
    let post_def = { name: this.definition.name };
    if (this.groupId) {
      GroupsAPI.updateSystemGroup(token, this.groupId, post_def)
        .then(() => {
          this.syncGroupSystems(token).then(() => {
            this.navigateToPrevious();
            this.errors = null;
          });
        })
        .catch((errors: any) => {
          this.errors = flattenErrors(errors);
        });
    } else {
      GroupsAPI.createSystemGroup(token, post_def)
        .then((groupResponse: StoredPVSystemGroup) => {
          this.groupId = groupResponse.object_id;
          this.syncGroupSystems(token).then(() => {
            this.navigateToPrevious();
            this.errors = null;
          });
        })
        .catch((errors: any) => {
          this.errors = flattenErrors(errors);
        });
    }
  }
  async syncGroupSystems(token: string): Promise<void> {
    if (typeof this.definition.systems !== "undefined") {
      let originalSystems = this.definition.systems.map(
        (system: StoredPVSystem) => {
          return system.object_id;
        }
      );
      let removedSystems = originalSystems.filter(
        (systemId: string) => !this.selectedSystems.includes(systemId)
      );
      let newSystems = this.selectedSystems.filter(
        (systemId: string) => !originalSystems.includes(systemId)
      );
      newSystems.forEach((systemId: string) => {
        GroupsAPI.addSystemToSystemGroup(token, this.groupId, systemId);
      });
      removedSystems.forEach((systemId: string) => {
        GroupsAPI.removeSystemFromSystemGroup(token, this.groupId, systemId);
      });
    }
  }
  async setSelectedSystems(): Promise<void> {
    if (this.definition.systems) {
      this.selectedSystems = this.definition.systems.map(
        (system: StoredPVSystem) => {
          return system.object_id;
        }
      );
    }
  }
}
</script>
<style scoped>
label {
  display: block;
  padding-bottom: 0.2em;
}
.definition-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.definition-inputs,
.definition-map {
  display: grid;
}
.map-wrapper {
  height: 500px;
  width: 50%;
}
ul.error-list {
  border: 1px solid #caa;
  border-radius: 0.5em;
  padding: 0.5em;
  background-color: #ecc;
  list-style: none;
}
ul.error-list li {
}
/* remove number in/decrement */
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  /* Firefox no in/decrement*/
  -moz-appearance: textfield;
  width: 3em;
}

.tracking {
  margin: 0.5em 3em 1em 0;
}
div.grid {
  display: grid;
  grid-template-columns: 4fr;
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
  border-bottom: 1px solid #ccc;
}

th,
tr {
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
</style>
