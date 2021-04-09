<template>
  <div class="systems" v-if="$auth.$auth.isAuthenticated">
    <h2>Systems</h2>
    <hr />
    <ul v-if="systems.length > 0" class="ul-grid">
      <li>
        <span class="ul-grid-item ul-grid-header">
          Name
        </span>
        <span class="ul-grid-item ul-grid-header">
          AC Capacity
        </span>
        <span class="ul-grid-item ul-grid-header">
          DC AC Ratio
        </span>
        <span class="ul-grid-item ul-grid-header">
          Tracking
        </span>
      </li>
      <li v-for="system of systems" :key="system.object_id">
        <details>
          <summary>
            <span class="ul-grid-item">{{ system.definition.name }}</span>
            <span class="ul-grid-item">{{ system.definition.ac_capacity }}</span>
            <span class="ul-grid-item">{{ system.definition.dc_ac_ratio }}</span>
            <span class="ul-grid-item">
              <template v-if="'backtracking' in system.definition.tracking">
                Single Axis
              </template>
              <template v-else>
                Fixed
              </template>
            </span>
          </summary>
          <div class="details-contents">
            <p>Location:  {{ }}</p>
            <p>other details</p>
          </div>
        </details>
      </li>
    </ul>
    <p v-else>No Systems yet. <a href="#">Create a new system.</a></p>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

@Component
export default class Systems extends Vue {
  systems!: Record<string, any>[];

  created(): void {
    // When the component is created, load the systems list.
    this.getSystems();
  }

  data(): Record<string, any> {
    return {
      systems: [],
    };
  }

  async getSystems(): Promise<void> {
    // Load the the list of systems from the api
    const token = await this.$auth.getTokenSilently();
    const response = await fetch(`/api/systems/`, {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
      }),
    });
    if (response.ok) {
      //const systemsList = await response.json();
      //this.systems = systemsList;
      this.systems = [
        {
          "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
          "object_type": "system",
          "created_at": "2020-12-01T01:23:00+00:00",
          "modified_at": "2020-12-01T01:23:00+00:00",
          "definition": {
            "name": "Test PV System",
            "boundary": {
              "nw_corner": {
                "latitude": 34.9,
                "longitude": -112.9
              },
              "se_corner": {
                "latitude": 33,
                "longitude": -111
              }
            },
            "ac_capacity": 10,
            "dc_ac_ratio": 1.2,
            "albedo": 0.2,
            "tracking": {
              "tilt": 20,
              "azimuth": 180
            }
          }
        }, {
          "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bhe0a9",
          "object_type": "system",
          "created_at": "2020-12-01T01:23:00+00:00",
          "modified_at": "2020-12-01T01:23:00+00:00",
          "definition": {
            "name": "Real PV System",
            "boundary": {
              "nw_corner": {
                "latitude": 34.9,
                "longitude": -112.9
              },
              "se_corner": {
                "latitude": 33,
                "longitude": -111
              }
            },
            "ac_capacity": 10,
            "dc_ac_ratio": 1.2,
            "albedo": 0.2,
            "tracking": {
              "tilt": 20,
              "azimuth": 180
            }
          }
        }
      ]
    } else {
      console.error("Could not load systems.");
    }
  }
}
</script>
<style>
.ul-grid {
  list-style: none;
}

.ul-grid li summary {
  padding: .5em;
  border: 1px solid black;
  background: white;
}
.details-contents{
  background: #CCC;
  padding: .5em;

}
</style>
