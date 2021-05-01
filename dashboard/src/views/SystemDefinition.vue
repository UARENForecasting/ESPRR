<template>
  <div class="system-definition-form">
    <h2 v-if="systemId">Update System</h2>
    <h2 v-else>Create New System</h2>
    <hr />
    <div v-if="definition" class="definition-container">
      <div id="definition-inputs">
        <ul class="error-list" v-if="errors">
          <li v-for="(field, error) in errors" :key="error">
            <b>{{ error }}:</b> {{ errors[error] }}
          </li>
        </ul>
        <form v-if="definition" id="system-definition" @submit="submitSystem">
          <label
            title="A name for this system. Most special characters beyond space, comma, hyphen, and parentheses are not allowed."
            >Name:
            <input
              type="text"
              maxlength="128"
              size="24"
              required
              pattern="^(?!\W+$)(?![_ ',\-\(\)]+$)[\w ',\-\(\)]*$"
              v-model="definition.name"
          /></label>
          <label title="AC Capacity of the system in MW"
            >AC Capacity (MW):
            <input
              type="number"
              step="any"
              min="0"
              required
              v-model.number="definition.ac_capacity"
          /></label>
          <label title="Ratio of installed DC capacity to AC capacity"
            >DC/AC Ratio:
            <input
              type="number"
              step="any"
              min="0"
              required
              v-model.number="definition.dc_ac_ratio"
          /></label>
          <label title="Sets Albedo for common surface types"
            >Surface Type:
            <select
              id="albedoSelect"
              name="albedoSelect"
              @change="changeAlbedo"
            >
              <option value="" disable selected>manually set albedo</option>
              <option
                v-for="k in Object.keys(surfaceTypes)"
                :key="k"
                :name="k"
                :value="k"
              >
                {{ k }}
              </option>
            </select>
          </label>
          <label title="Albedo of the ground where system is installed"
            >Albedo:
            <input
              type="number"
              step="any"
              min="0"
              max="1"
              required
              v-model.number="definition.albedo"
          /></label>

          <fieldset class="tracking">
            <legend>Panel Orientation/Tracking</legend>
            <label
              title="Choose between PV panels that are mounted at a fixed orientation or on a single-axis tracking system"
            >
              Tracking Type:
              <input type="radio" v-model="trackingType" value="fixed" />Fixed
              Tilt
              <input
                type="radio"
                v-model="trackingType"
                value="singleAxis"
              />Single Axis
            </label>
            <fieldset class="fixed" v-if="trackingType == 'fixed'">
              <label title="Tilt of the panels in degrees from horizontal">
                Tilt:
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="90"
                  required
                  v-model.number="definition.tracking.tilt"
                />
              </label>
              <label
                title="Azimuth of the panels in degrees from North. 180 == South"
              >
                Azimuth:
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="360"
                  required
                  v-model.number="definition.tracking.azimuth"
                />
              </label>
            </fieldset>
            <fieldset class="fixed" v-else>
              <label
                title="Tilt (in degrees) of the axis of rotation with respect to horizontal. Typically 0."
              >
                Axis Tilt:
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="90"
                  required
                  v-model.number="definition.tracking.axis_tilt"
                />
              </label>
              <label
                title="The compass direction along which the axis of rotation lies. Measured in decimal degrees east of north. Typically 0."
              >
                Axis Azimuth:
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="360"
                  required
                  v-model.number="definition.tracking.axis_azimuth"
                />
              </label>
              <label>
                Ground Coverage Ratio:
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="1"
                  required
                  v-model.number="definition.tracking.gcr"
                />
              </label>
              <label
                title='Controls whether the tracker has the capability to "backtrack" to avoid row-to-row shading. False denotes no backtrack capability. True denotes backtrack capability.'
              >
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
          <button type="submit" :disabled="!boundarySelected">
            <template v-if="systemId">Update</template
            ><template v-else>Create</template> System</button
          ><span v-if="!boundarySelected"
            >You must place the system on the map to the left before
            creation.</span
          >
        </form>
      </div>
      <div id="definition-map" v-if="this.systems">
        <system-map
          :editable="true"
          :system="definition"
          :all_systems="otherSystems"
          :dc_capacity="dcCapacity"
          @bounds-updated="updateBounds"
        />
      </div>
    </div>
    <div v-else>The System could not be found.</div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import * as SystemsApi from "@/api/systems";
import flattenErrors from "@/api/errors";
import SystemMap from "@/components/Map.vue";
import SurfaceTypes from "@/constants/surface_albedo.json";

import {
  StoredPVSystem,
  PVSystem,
  FixedTracking,
  SingleAxisTracking,
  BoundingBox,
} from "@/models";

Vue.component("system-map", SystemMap);

interface HTMLInputEvent extends Event {
  target: HTMLInputElement & EventTarget;
}

@Component
export default class SystemDefinition extends Vue {
  @Prop() systemId!: string;

  definition!: PVSystem;
  trackingType!: string;
  systems!: Array<StoredPVSystem>;
  errors!: Record<string, string> | null;
  surfaceTypes: Record<string, number> = SurfaceTypes;

  data(): Record<string, any> {
    return {
      definition: this.definition,
      trackingType: this.trackingType,
      systems: null,
      errors: null,
    };
  }

  created(): void {
    if (this.systemId) {
      this.loadSystem();
      this.loadSystems();
    } else {
      // @ts-expect-error don't expect boundary at creation
      this.definition = {
        name: "New System",
        tracking: {
          tilt: 0,
          azimuth: 180,
        },
        albedo: 0.2,
        ac_capacity: 1,
        dc_ac_ratio: 1.2,
      };
      this.trackingType = "fixed";
      this.loadSystems();
    }
  }

  async loadSystem(): Promise<void> {
    // fetch system from api and set definition and set trackingType
    const token = await this.$auth.getTokenSilently();
    SystemsApi.getSystem(token, this.systemId)
      .then((system: StoredPVSystem) => {
        this.definition = system.definition;
        if ("axis_tilt" in this.definition.tracking) {
          this.trackingType = "singleAxis";
        } else {
          this.trackingType = "fixed";
        }
      })
      .catch(() => {
        // 404 case, don't set definition
        return;
      });
  }

  validateSystem(): boolean {
    // validate the system with the systems/check endpoint
    /* istanbul ignore next */
    return true;
  }

  async loadSystems(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsApi.listSystems(token)
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
    if ("returnTo" in this.$route.query) {
      if (this.$route.query.returnTo == "details") {
        this.$router.push({
          name: "System Details",
          params: {
            systemId: this.systemId,
          },
        });
      } else {
        this.$router.push({ name: "Systems" });
      }
    } else {
      this.$router.push({ name: "Systems" });
    }
  }

  async submitSystem(e: Event): Promise<void> {
    e.preventDefault();
    // validate and post system
    const token = await this.$auth.getTokenSilently();
    if (this.systemId) {
      SystemsApi.updateSystem(token, this.systemId, this.definition)
        .then((systemResponse: StoredPVSystem) => {
          SystemsApi.startProcessing(
            token,
            systemResponse.object_id,
            "NSRDB_2019"
          ).then(() => {
            this.navigateToPrevious();
            this.errors = null;
          });
        })
        .catch((errors: any) => {
          this.errors = flattenErrors(errors);
        });
    } else {
      SystemsApi.createSystem(token, this.definition)
        .then((response: any) => {
          SystemsApi.startProcessing(
            token,
            response.object_id,
            "NSRDB_2019"
          ).then(() => {
            this.navigateToPrevious();
            this.errors = null;
          });
        })
        .catch((errors: any) => {
          this.errors = flattenErrors(errors);
        });
    }
  }

  changeAlbedo(e: HTMLInputEvent): void {
    this.definition.albedo = this.surfaceTypes[e.target.value];
  }

  @Watch("trackingType")
  changeTracking(newTrackingType: string, oldTrackingType: string): void {
    // Change the model used for tracking on the system definition
    // when the tracking type changes.
    let newParameters: FixedTracking | SingleAxisTracking;
    if (oldTrackingType == newTrackingType || !oldTrackingType) {
      newParameters = this.definition.tracking;
    } else {
      if (newTrackingType == "fixed") {
        const currentParams = this.definition.tracking as SingleAxisTracking;
        newParameters = {
          tilt: currentParams.axis_tilt,
          azimuth: currentParams.axis_azimuth,
        };
      } else {
        const currentParams = this.definition.tracking as FixedTracking;
        newParameters = {
          axis_tilt: currentParams.tilt,
          axis_azimuth: currentParams.azimuth,
          gcr: 0.4,
          backtracking: true,
        };
      }
    }
    this.definition.tracking = newParameters;
  }

  updateBounds(newBounds: BoundingBox): void {
    this.$set(this.definition, "boundary", newBounds);
  }
  get dcCapacity(): number | null {
    if (this.definition.ac_capacity && this.definition.dc_ac_ratio) {
      return this.definition.ac_capacity * this.definition.dc_ac_ratio;
    } else {
      return null;
    }
  }

  get otherSystems(): Array<StoredPVSystem> {
    let otherSystems: Array<StoredPVSystem>;
    if (this.systemId) {
      otherSystems = this.systems.filter((system: StoredPVSystem) => {
        return system.object_id != this.systemId;
      });
    } else {
      otherSystems = this.systems;
    }
    return otherSystems;
  }
  get boundarySelected(): boolean {
    return "boundary" in this.definition;
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
</style>
