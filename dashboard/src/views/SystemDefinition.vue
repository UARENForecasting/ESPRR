<template>
  <div class="system-definition-form">
    <h2 v-if="systemId">Create New System</h2>
    <h2 v-else>Create New System</h2>
    <form v-if="definition" id="system-definition" @submit="submitSystem">
      <label>Name: <input type="text" v-model="definition.name" /></label>
      <label
        >AC Capacity:
        <input type="number" step="any" v-model.number="definition.ac_capacity"
      /></label>
      <label
        >DC/ AC Ratio:
        <input type="number" step="any" v-model.number="definition.dc_ac_ratio"
      /></label>
      <label
        >Albedo:
        <input type="number" step="any" v-model.number="definition.albedo"
      /></label>

      <fieldset class="boundary">
        <!-- Replace with vue-leaflet/map selection -->
        <legend>Boundary</legend>
        <fieldset class="nw_corner">
          <legend>Northwest Corner</legend>
          <label>
            Latitude:
            <input
              type="number"
              step="any"
              v-model.number="definition.boundary.nw_corner.latitude"
            />
          </label>
          <label>
            Longitude:
            <input
              type="number"
              step="any"
              v-model.number="definition.boundary.nw_corner.longitude"
            />
          </label>
        </fieldset>
        <fieldset class="se_corner">
          <legend>Southeast Corner</legend>
          <label>
            Latitude:
            <input
              type="number"
              step="any"
              v-model.number="definition.boundary.se_corner.latitude"
            />
          </label>
          <label>
            Longitude:
            <input
              type="number"
              step="any"
              v-model.number="definition.boundary.se_corner.longitude"
            />
          </label>
        </fieldset>
      </fieldset>
      <fieldset class="tracking">
        <legend>Tracking</legend>
        <label>
          Tracking Type:
          <input
            type="radio"
            @change="changeTracking"
            v-model="trackingType"
            value="fixed"
          />Fixed
          <input
            type="radio"
            @change="changeTracking"
            v-model="trackingType"
            value="singleAxis"
          />Single Axis
        </label>
        <fieldset class="fixed" v-if="trackingType == 'fixed'">
          <label>
            Tilt:
            <input
              type="number"
              step="any"
              v-model.number="definition.tracking.tilt"
            />
          </label>
          <label>
            Azimuth:
            <input
              type="number"
              step="any"
              v-model.number="definition.tracking.azimuth"
            />
          </label>
        </fieldset>
        <fieldset class="fixed" v-else>
          <label>
            Axis Tilt:
            <input
              type="number"
              step="any"
              v-model.number="definition.tracking.axis_tilt"
            />
          </label>
          <label>
            Axis Azimuth:
            <input
              type="number"
              step="any"
              v-model.number="definition.tracking.axis_azimuth"
            />
          </label>
          <label>
            Ground Coverage Ratio:
            <input
              type="number"
              step="any"
              v-model.number="definition.tracking.gcr"
            />
          </label>
          <label>
            Backtracking:
            <input
              type="radio"
              v-model="definition.tracking.backtracking"
              :value="true"
            />True
            <input
              type="radio"
              v-model="definition.tracking.backtracking"
              :value="false"
            />False
          </label>
        </fieldset>
      </fieldset>
      <button type="submit">Create System</button>
    </form>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop } from "vue-property-decorator";
import * as SystemsApi from "@/api/systems";
import { PVSystem, FixedTracking, SingleAxisTracking } from "@/models";

@Component
export default class SystemDefinition extends Vue {
  @Prop() systemId!: string;

  definition!: PVSystem;
  trackingType!: string;

  data(): Record<string, any> {
    return {
      definition: this.definition,
      trackingType: this.trackingType,
    };
  }

  created(): void {
    if (this.systemId) {
      this.loadSystem();
    } else {
      this.definition = {
        name: "New System",
        boundary: {
          nw_corner: {
            latitude: 33.44,
            longitude: -112.07,
          },
          se_corner: {
            latitude: 33.43,
            longitude: -112.06,
          },
        },
        tracking: {
          tilt: 0,
          azimuth: 0,
        },
        albedo: 0.2,
        ac_capacity: 1,
        dc_ac_ratio: 1.2,
      };
      this.trackingType = "fixed";
    }
  }

  loadSystem(): void {
    // fetch system from api and set definition and set trackingType
    return;
  }

  validateSystem(): boolean {
    // validate the system with the systems/check endpoint
    return true;
  }

  async submitSystem(e: Event): Promise<void> {
    e.preventDefault();
    // validate and post system
    const token = await this.$auth.getTokenSilently();
    SystemsApi.createSystem(token, this.definition)
      .then(() => {
        this.$router.push({ name: "Systems" });
      })
      .catch((errors: any) => {
        // TODO :display errors to users
        console.log(errors);
      });
  }

  changeTracking(trackingType: string): void {
    // Change the model used for tracking on the system definition
    // when the tracking type changes.
    let newParameters: FixedTracking | SingleAxisTracking;
    if (this.trackingType == trackingType) {
      newParameters = this.definition.tracking;
    } else {
      if (trackingType == "fixed") {
        newParameters = {
          tilt: 0,
          azimuth: 0,
        };
      } else {
        newParameters = {
          axis_tilt: 0,
          axis_azimuth: 0,
          gcr: 0,
          backtracking: false,
        };
      }
    }
    this.definition.tracking = newParameters;
  }
}
</script>
<style scoped>
label {
  display: block;
}
</style>
