<template>
  <div class="system-definition-form">
    <h2 >Create New Distributed System Group</h2>
    <p>Creates multiple systems given total desired AC capacity, number of
      systems, and distance between sites. Systems created this way will be
      identical other than location, but may be edited after creation.
    <hr />
    <div v-if="definition" class="definition-container">
      <div id="definition-inputs">
        <ul class="error-list" v-if="errors">
          <li v-for="(field, error) in errors" :key="error">
            <b>{{ error }}:</b> {{ errors[error] }}
          </li>
        </ul>
        <form v-if="definition" id="distributed-group-definition" @submit="submit">
          <label
            title="A name for this space, comma, hyphen, and parentheses are not allowed."
            >Name:
            <input
              type="text"
              maxlength="128"
              size="24"
              required
              pattern="^(?!\W+$)(?![_ ',\-\(\)]+$)[\w ',\-\(\)]*$"
              v-model="definition.name"
          /></label>
          <label title="Cumulative AC Capacity of desired systems in MW"
            >Total AC Capacity (MW):
            <input
              type="number"
              step="any"
              min="0"
              required
              v-model.number="totalAcCapacity"
          /></label>
          <label title="Number of systems"
            >Number of systems:
            <input
              type="number"
              step="1"
              min="1"
              required
              v-model.number="numberOfSystems"
          /></label>
          <label title="Distance between systems"
            >Distance between systems (km):
            <input
              type="number"
              step="any"
              min="0"
              required
              v-model.number="distanceBetweenSystems"
          /></label>
          <fieldset>
          <legend>System Parameters</legend>
          <label>AC Capacity (MW): {{ (totalAcCapacity / numberOfSystems).toFixed(2) }}</label>
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
          </fieldset>
          <button type="submit" :disabled="!boundarySelected">
            Create Distributed Group</button
          ><span v-if="!boundarySelected"
            >You must place the systems on the map to the left before
            creation.</span
          >
        </form>
      </div>
      <div id="definition-map" v-if="this.systems">
        <distributed-system-map
          :editable="true"
          :system="definition"
          :all_systems="otherSystems"
          :dc_capacity="dcCapacity"
          :numSystems="numberOfSystems"
          :distanceBetween="distanceBetweenSystems"
          @bounds-updated="updateBounds"
        />
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import * as SystemsApi from "@/api/systems";
import * as GroupsAPI from "@/api/systemGroups";
import flattenErrors from "@/api/errors";
import DistributedGroupMap from "@/components/DistributedMap.vue";
import SurfaceTypes from "@/constants/surface_albedo.json";

import {
  StoredPVSystem,
  StoredPVSystemGroup,
  PVSystem,
  FixedTracking,
  SingleAxisTracking,
  BoundingBox,
} from "@/models";

Vue.component("distributed-system-map", DistributedGroupMap);

interface HTMLInputEvent extends Event {
  target: HTMLInputElement & EventTarget;
}

@Component
export default class DistributedGroupDefinition extends Vue {
  @Prop() systemId!: string;
  @Prop() dataset!: string;

  definition!: PVSystem;
  trackingType!: string;
  systems!: Array<StoredPVSystem>;
  errors!: Record<string, string> | null;
  surfaceTypes: Record<string, number> = SurfaceTypes;

  totalAcCapacity!: number;
  numberOfSystems!: number;
  distanceBetweenSystems!: number;
  systemBounds!: Array<BoundingBox>;

  data(): Record<string, any> {
    return {
      definition: this.definition,
      trackingType: this.trackingType,
      seedPoint: null,
      systems: null,
      errors: null,
      numberOfSystems: 2,
      distanceBetweenSystems: 1,
      totalAcCapacity: 1,
      systemBounds: []
    };
  }

  created(): void {
    // @ts-expect-error don't expect boundary at creation
    this.definition = {
      name: "New Distributed Group",
      tracking: {
        tilt: 0,
        azimuth: 180,
      },
      albedo: 0.2,
      dc_ac_ratio: 1.2,
    };
    this.trackingType = "fixed";
    this.loadSystems();
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

  async submit(e: Event): Promise<void> {
    e.preventDefault();
    // validate and post system
    const token = await this.$auth.getTokenSilently();
    // TODO: join definition into actual system definition.
    //   and name with name + number
    let newSystemIds = [];
    // look in systems for names, warn user.
    // TODO: create all systems - Sanity check that systems don't exist first
    let newSystemDefinitions = this.systemBounds.map(
      (bounds:BoundingBox, i: number) => {
        return {
          ...this.definition,
          name: `${this.definition.name} System ${i}`,
          boundary: bounds,
          ac_capacity: this.totalAcCapacity / this.numberOfSystems
        }
      }
    );
    console.log(newSystemDefinitions);
    let existingSystems = this.systems.map((sys: StoredPVSystem) => sys.definition.name);
    if (newSystemDefinitions.some((sys: PVSystem) => existingSystems.includes(sys.name))) {
      console.error("ahh. panic");
    }
    let systemPromises = [];
    for (const sys of newSystemDefinitions) {
      systemPromises.push(SystemsApi.createSystem(token, sys));
      // TODO some error handling here?
      //  .then((response: any) => {
      //    SystemsApi.startProcessing(
      //      token,
      //      response.object_id,
      //      "NSRDB_2019"
      //    ).then(() => {
      //      this.navigateToPrevious();
      //      this.errors = null;
      //    });
      //  })
      //  .catch((errors: any) => {
      //    this.errors = flattenErrors(errors);
      //  });
    }
    // TODO: create system group and add all systems to said group
    // 1 - create group
    // 2 - for system in systemIds add to group
    let systemIds = await Promise.all(systemPromises).then(
        (responses:any) => responses.map((response:any) =>response.object_id)
    );
    // TODO: send the user to the group page
    console.log("Made all these systems: ", systemIds);
    let groupDef = { name: this.definition.name };
    let groupId = await GroupsAPI.createSystemGroup(token, groupDef)
      .then((groupResponse: StoredPVSystemGroup) => groupResponse.object_id);
    let sysAdditionPromises = []
    for (const systemId of systemIds) {
      sysAdditionPromises.push(GroupsAPI.addSystemToSystemGroup(
        token,
        groupId,
        systemId
      ))
    }
    let allAdded = await Promise.all(sysAdditionPromises);
    this.$router.push({
      name: "Group Details",
      params: {
        groupId
      }
    });
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

  updateBounds(newBounds: Array<BoundingBox>): void {
    this.systemBounds =  newBounds;
  }
  get dcCapacity(): number | null {
    if (this.totalAcCapacity && this.definition.dc_ac_ratio) {
      return this.totalAcCapacity * this.definition.dc_ac_ratio;
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
    return this.systemBounds.length > 0;
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
