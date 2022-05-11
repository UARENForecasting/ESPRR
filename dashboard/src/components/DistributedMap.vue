<template>
  <div class="l-wrapper">
    <l-map
      ref="systemMap"
      :zoom="zoom"
      :center="center"
      @ready="mapReady"
      @click="placeSystem"
    >
      <l-control-layers
        position="topright"
        :collapsed="false"
      ></l-control-layers>
      <l-tile-layer :url="url" :attribution="attribution"> </l-tile-layer>
      <l-control-scale
        position="bottomleft"
        :imperial="false"
        :metric="true"
      ></l-control-scale>

      <template v-if="groupSystems">
        <l-rectangle
          v-for="(latlng, i) in groupSystems"
          :key="i"
          name="name"
          :bounds="latlng"
          color="green"
          fillColor="green"
        >
        </l-rectangle>
      </template>
      <l-layer-group name="All Systems" layer-type="overlay" v-if="all_systems">
        <l-rectangle
          v-for="system of all_systems"
          :key="system.object_id"
          :bounds="createRectangle(system.definition.boundary)"
        >
        </l-rectangle>
      </l-layer-group>
    </l-map>
    <div class="map-prompt">
      <fieldset>
        <legend>Placement Strategy</legend>
        <p>
          Select a placement strategy for the distributed plants. The
          <i>Line</i> strategy places plants on a North/South or East/West line.
          The <i>grid</i> strategy will arrange the plants in an approximate
          square.
        </p>
        <label>
          Line
          <input
            style="width: 3em"
            type="radio"
            value="line"
            v-model="strategy"
            @change="adjustForCapacity"
          />
        </label>
        <label>
          Grid
          <input
            style="width: 3em"
            type="radio"
            value="grid"
            v-model="strategy"
            @change="adjustForCapacity"
          /> </label
        ><br />
        <fieldset v-if="strategy == 'line'">
          <legend>Line orientation</legend>
          <label>
            East/West
            <input
              style="width: 3em"
              type="radio"
              value="EW"
              v-model="lineOrientation"
              @change="adjustForCapacity"
            />
          </label>
          <label>
            North/South
            <input
              style="width: 3em"
              type="radio"
              value="NS"
              v-model="lineOrientation"
              @change="adjustForCapacity"
            />
          </label>
        </fieldset>
      </fieldset>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import GeoUtil from "leaflet-geometryutil";

import L from "leaflet";
import {
  LMap,
  LTileLayer,
  LMarker,
  LControlScale,
  LControlLayers,
  LLayerGroup,
  LRectangle,
} from "vue2-leaflet";

import StaticAreaRectangle from "@/components/leafletLayers/StaticAreaRectangle.vue";

import { BoundingBox } from "@/models";

import { PVSystem, StoredPVSystem } from "@/models";

import GetColor from "@/utils/Colors";

Vue.component("l-map", LMap);
Vue.component("l-tile-layer", LTileLayer);
Vue.component("l-marker", LMarker);
Vue.component("l-control-scale", LControlScale);
Vue.component("l-control-layers", LControlLayers);
Vue.component("l-layer-group", LLayerGroup);
Vue.component("l-rectangle", LRectangle);
Vue.component("static-area-rectangle", StaticAreaRectangle);

@Component
export default class DistributedGroupMap extends Vue {
  @Prop() system!: PVSystem;
  @Prop({ default: () => [] }) systems!: Array<StoredPVSystem>;
  @Prop({ default: false }) editable!: boolean;
  @Prop() dc_capacity!: number;
  @Prop() all_systems!: Array<StoredPVSystem>;
  @Prop() numSystems!: number;
  @Prop() distanceBetween!: number;

  url!: string;
  attribution!: string;
  zoom!: number;
  center!: L.LatLng;
  draggable!: boolean;
  scaling!: boolean;
  map!: L.Map;
  aspectInputX!: number;
  aspectInputY!: number;
  aspectX!: number;
  aspectY!: number;
  initialized!: boolean;
  strategy!: string;
  groupSystems!: Array<L.LatLngBounds>;
  lineOrientation!: string;

  mapReady(): void {
    // @ts-expect-error accessing Leaflet API
    this.map = this.$refs.systemMap.mapObject;
    this.initialize();
  }

  initialize(): void {
    this.draggable = true;
    if (this.editable) {
      this.scaling = true;
    } else {
      this.draggable = false;
      this.scaling = false;
    }

    this.initialized = true;
  }

  data(): any {
    return {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      zoom: 11,
      center: L.latLng(33.4484, -112.074),
      aspectX: 1,
      aspectY: 1,
      aspectInputX: 1,
      aspectInputY: 1,
      initialized: false,
      strategy: "line",
      lineOrientation: "EW",
      groupSystems: [],
    };
  }

  get sitePolygon(): Array<L.LatLng> | null {
    if (this.bounds) {
      return [
        L.latLng(this.bounds.getNorth(), this.bounds.getWest()),
        L.latLng(this.bounds.getNorth(), this.bounds.getEast()),
        L.latLng(this.bounds.getSouth(), this.bounds.getEast()),
        L.latLng(this.bounds.getSouth(), this.bounds.getWest()),
      ];
    } else {
      return null;
    }
  }

  createPolygon(boundingBox: BoundingBox): Array<L.LatLng> {
    return [
      L.latLng(boundingBox.nw_corner.latitude, boundingBox.nw_corner.longitude),
      L.latLng(boundingBox.nw_corner.latitude, boundingBox.se_corner.longitude),
      L.latLng(boundingBox.se_corner.latitude, boundingBox.se_corner.longitude),
      L.latLng(boundingBox.se_corner.latitude, boundingBox.nw_corner.longitude),
    ];
  }

  createRectangle(boundingBox: BoundingBox): Array<L.LatLng> {
    return [
      L.latLng(boundingBox.nw_corner.latitude, boundingBox.nw_corner.longitude),
      L.latLng(boundingBox.se_corner.latitude, boundingBox.se_corner.longitude),
    ];
  }

  getGroupBounds(): L.LatLngBounds | null {
    let all_bounds = this.groupSystems;
    if (all_bounds.length > 0) {
      let north = Math.max(...all_bounds.map((b) => b.getNorth()));
      let east = Math.min(...all_bounds.map((b) => b.getEast()));
      let west = Math.max(...all_bounds.map((b) => b.getWest()));
      let south = Math.min(...all_bounds.map((b) => b.getSouth()));
      return L.latLngBounds(L.latLng(north, west), L.latLng(south, east));
    } else {
      return null;
    }
  }
  @Watch("dc_capacity")
  @Watch("numSystems")
  @Watch("distanceBetween")
  adjustForCapacity(): void {
    if (this.bounds) {
      // increase the size of the system at the current center
      this.initializePolygons();
    }
  }
  areaFromCapacity(): number {
    // roughly 40MW/km^2  assumed
    let totalCapacity = this.dc_capacity / this.numSystems;
    return totalCapacity / 40;
  }

  get bounds(): L.LatLngBounds | null {
    if (this.groupSystems) {
      return this.getGroupBounds();
    } else {
      return null;
    }
  }

  placeLineStrategy(squareSideLength: number): Array<L.LatLngBounds> {
    const sitePolygons = [];
    for (let i = 0; i < this.numSystems; i++) {
      let oneCenter = this.center;
      // initialAngle is set perpendicular to the ling to be drawn. 0 is north
      // so that we can toggle +/- 90 degrees to point either direction
      let initialAngle = 90;
      if (this.lineOrientation == "EW") {
        initialAngle = 0;
      }
      if (i > 0) {
        oneCenter = GeoUtil.destination(
          this.center,
          initialAngle + 90 * Math.pow(-1, i), // alternate placement right to left
          this.distanceBetween * 1000 * Math.ceil(i / 2) // km to m
        );
      }
      const boundsOfArea = oneCenter.toBounds(squareSideLength * 1000);
      sitePolygons.push(boundsOfArea);
    }
    return sitePolygons;
  }
  /* Places systems in a box pattern by determining a direction from the last
   * placed system. Uses a concept of "stages" to maintain shape. The example
   * below uses numbers to indicate at which point a system was placed
   *       4 4 4 4 4
   *       3 2 2 2 4
   *       3 1 1 2 4
   *       3 1 1 2 4
   *       3 3 3 3 4
   */
  placeGridStrategy(squareSideLength: number): Array<L.LatLngBounds> {
    const sitePolygons = [];
    let last = this.center;
    let oneCenter = this.center;

    let direction = 0;
    for (let i = 0; i < this.numSystems; i++) {
      if (i > 0) {
        let stage = Math.floor(Math.sqrt(i));
        let step = i - Math.pow(stage, 2);
        if (stage == 1) {
          // step 1-3 go left, down, right
          direction = 0 - 90 * i;
        } else if (stage % 2 == 0) {
          // stage even go up, then left
          if (step > 0 && step <= stage) {
            // go up stage , increasing the height of the grid by 1
            direction = 0.0;
          } else if (step > stage) {
            // go left until the next stage
            direction = 270.0;
          }
        } else {
          // stage = odd go down, then right
          if (step > 0 && step <= stage) {
            // go down stage, increasing the height of the grid by 1
            direction = 180.0;
          } else if (step > stage) {
            // go right until the next stage
            direction = 90.0;
          }
        }
        // If step was 0, continue the same direction as before. This
        // will always be left/right increasing the width of the box on
        // each stage change
        oneCenter = GeoUtil.destination(
          last,
          direction,
          this.distanceBetween * 1000 // convert km to m
        );
      }
      last = oneCenter;

      const boundsOfArea = oneCenter.toBounds(squareSideLength * 1000);
      sitePolygons.push(boundsOfArea);
    }
    return sitePolygons;
  }

  getSitePolygons(): Array<L.LatLngBounds> {
    // create a square based on provided area
    const area = this.areaFromCapacity();
    // determine length of one side of square from area
    const squareSideLength = Math.sqrt(area);
    //for (let i = 0; i < this.numSystems; i++) {
    if (this.strategy == "line") {
      return this.placeLineStrategy(squareSideLength);
    } else {
      return this.placeGridStrategy(squareSideLength);
    }
  }

  initializePolygons(): void {
    this.groupSystems = this.getSitePolygons();
    this.$emit(
      "bounds-updated",
      this.groupSystems.map((bounds: L.LatLngBounds) =>
        this.leafletBoundsToBoundingBox(bounds)
      )
    );
  }
  placeSystem(event: L.LeafletMouseEvent): void {
    if (this.bounds == null) {
      this.center = event.latlng;
      this.initializePolygons();
    }
  }

  boundingBoxToLeafletBounds(bb: BoundingBox): L.LatLngBounds {
    return L.latLngBounds(
      L.latLng(bb.nw_corner.latitude, bb.nw_corner.longitude),
      L.latLng(bb.se_corner.latitude, bb.se_corner.longitude)
    );
  }

  leafletBoundsToBoundingBox(lb: L.LatLngBounds): BoundingBox {
    return {
      nw_corner: {
        latitude: lb.getNorth(),
        longitude: lb.getWest(),
      },
      se_corner: {
        latitude: lb.getSouth(),
        longitude: lb.getEast(),
      },
    };
  }

  emitSelection(system: StoredPVSystem): void {
    // Emit an event so parent components can update highlighting/selection
    this.$emit("new-selection", system);
  }
  reshape(): void {
    if (this.center != null) {
      this.initializePolygons();
    }
  }

  @Watch("bounds", { deep: true })
  fitMapBounds(): void {
    this.map.fitBounds(this.bounds!, { animate: true });
  }
  getColor(index: number): string {
    return GetColor(index);
  }
}
</script>
<style scoped>
.l-wrapper {
  width: 100%;
  height: 40vh;
}
.map-prompt {
  display: grid;
  background-color: #eaeaea;
  padding: 0 1em;
}
/* remove number in/decrement */
/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type="number"] {
  -moz-appearance: textfield;
}
</style>
