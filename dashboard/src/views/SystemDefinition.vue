<template>
  <div class="system-definition-form">
    <h2 v-if="systemId">Update System</h2>
    <h2 v-else>Create New System</h2>
    <hr />
    <div v-if="definition" class="definition-container">
      <div id="definition-inputs">
        <form v-if="definition" id="system-definition" @submit="submitSystem">
          <label>Name: <input type="text" v-model="definition.name" /></label>
          <label
            >AC Capacity:
            <input
              type="number"
              step="any"
              v-model.number="definition.ac_capacity"
          /></label>
          <label
            >DC/ AC Ratio:
            <input
              type="number"
              step="any"
              v-model.number="definition.dc_ac_ratio"
          /></label>
          <label
            >Albedo:
            <input type="number" step="any" v-model.number="definition.albedo"
          /></label>

          <fieldset class="tracking">
            <legend>Tracking</legend>
            <label>
              Tracking Type:
              <input type="radio" v-model="trackingType" value="fixed" />Fixed
              <input
                type="radio"
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
          <button type="submit">
            <template v-if="systemId">Update</template
            ><template v-else>Create</template> System
          </button>
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
import SystemMap from "@/components/Map.vue";

import {
  StoredPVSystem,
  PVSystem,
  FixedTracking,
  SingleAxisTracking,
  BoundingBox,
} from "@/models";

Vue.component("system-map", SystemMap);

@Component
export default class SystemDefinition extends Vue {
  @Prop() systemId!: string;

  definition!: PVSystem;
  trackingType!: string;
  systems!: Array<StoredPVSystem>;

  data(): Record<string, any> {
    return {
      definition: this.definition,
      trackingType: this.trackingType,
      systems: null,
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
          azimuth: 0,
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
      .catch((errors: any) => {
        // 404 case, don't set definition
        console.log(errors);
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
        console.log(errors);
      });
  }

  async submitSystem(e: Event): Promise<void> {
    e.preventDefault();
    // validate and post system
    const token = await this.$auth.getTokenSilently();
    if (this.systemId) {
      SystemsApi.updateSystem(token, this.systemId, this.definition)
        .then(() => {
          this.$router.push({ name: "Systems" });
        })
        .catch((errors: any) => {
          // TODO :display errors to users
          console.log(errors);
        });
    } else {
      SystemsApi.createSystem(token, this.definition)
        .then(() => {
          this.$router.push({ name: "Systems" });
        })
        .catch((errors: any) => {
          // TODO :display errors to users
          console.log(errors);
        });
    }
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
          gcr: 0,
          backtracking: false,
        };
      }
    }
    this.definition.tracking = newParameters;
  }

  updateBounds(newBounds: BoundingBox): void {
    this.definition.boundary = newBounds;
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
}
</script>
<style scoped>
label {
  display: block;
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
</style>
