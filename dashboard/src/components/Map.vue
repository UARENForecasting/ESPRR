<template>
  <div class="map-component-wrapper">
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
        <static-area-rectangle
          v-if="sitePolygon"
          :draggable="editable"
          :scaling="false"
          :rotation="false"
          :latLngs="sitePolygon"
          color="#0A0"
          fillColor="#0A0"
          @transformed="handleTransformation"
          @scaleend="handleTransformation"
        />
        <template v-if="systems">
          <l-rectangle
            v-for="(system, i) in systems"
            :key="system.object_id"
            :name="system.definition.name"
            :bounds="createRectangle(system.definition.boundary)"
            :color="getColor(i)"
            :fillColor="getColor(i)"
            @click="emitSelection(system)"
          >
          </l-rectangle>
        </template>
        <l-layer-group
          name="All Systems"
          layer-type="overlay"
          v-if="all_systems"
        >
          <l-rectangle
            v-for="system of all_systems"
            :key="system.object_id"
            :bounds="createRectangle(system.definition.boundary)"
            @click="emitSelection(system)"
          >
          </l-rectangle>
        </l-layer-group>
        <l-polyline
          :stroke="true"
          :lat-lngs="transmissionPath"
          v-if="showTransmissionPath"
        />
        <l-layer-group
          name="Transmission Lines"
          layer-type="overlay"
          v-if="transmission"
          :visible="false"
        >
          <l-geo-json
            :geojson="transmission"
            :options-style="{ color: '#444', weight: 2 }"
            :options="options"
            @ready="setTransmissionLayers"
            @click="selectTransmission"
          >
          </l-geo-json>
        </l-layer-group>
      </l-map>
    </div>
    <div class="map-prompt">
      <p v-if="editable && !bounds">
        Click on the map to place the system. The system will be represented by
        a square with an area corresponding to its DC capacity at a density of
        40 Megawatts per square kilometer.
      </p>
      <div v-if="editable && bounds">
        <p v-if="editable && bounds">
          Click and drag to move the sytem's location. Use the
          <i>Aspect Ratio</i>
          boxes below to adjust the shape of the system's bounding box.
        </p>
        <fieldset>
          <legend>Aspect Ratio</legend>
          <label>
            North-South
            <input
              style="width: 3em"
              type="number"
              step="any"
              min="1"
              max="100"
              v-model.number="aspectInputY"
            />
          </label>
          <label>
            East-West
            <input
              style="width: 3em"
              step="any"
              type="number"
              min="1"
              max="100"
              v-model.number="aspectInputX"
            /> </label
          ><br />
          <span v-if="aspectInputsInvalid" class="warning-text"
            >Aspect ratio dimensions must be between 1 and 100.</span
          >
        </fieldset>
      </div>
      <div v-if="closestTransmission">
        <h3>Closest Transmission</h3>
        <ul>
          <li>
            <b>Distance:</b> {{ transDistance }} km ({{
              (transDistance * 0.62).toFixed(2)
            }}
            mi)
            <button @click="showTransmissionPath = !showTransmissionPath">
              Toggle path to transmission
            </button>
          </li>
          <li>
            <b>Owner:</b>
            {{ closestTransmission.layer.feature.properties.OWNER }}
          </li>
          <li>
            <b>Type:</b> {{ closestTransmission.layer.feature.properties.TYPE }}
          </li>
          <li>
            <b>Status:</b>
            {{ closestTransmission.layer.feature.properties.STATUS }}
          </li>
          <li>
            <b>As of:</b>
            {{ closestTransmission.layer.feature.properties.VAL_DATE }}
          </li>
        </ul>
        <p>
          Transmission line data provided by
          <a href="https://www.ornl.gov/">Oak Ridge National Lab</a> and
          accessed through
          <a href="https://hifld-geoplatform.opendata.arcgis.com/">HIFLD</a>.
        </p>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";

import L from "leaflet";
import {
  LMap,
  LTileLayer,
  LMarker,
  LControlScale,
  LControlLayers,
  LLayerGroup,
  LRectangle,
  LGeoJson,
  LPolyline,
} from "vue2-leaflet";
import GeoUtil from "leaflet-geometryutil";

import StaticAreaRectangle from "@/components/leafletLayers/StaticAreaRectangle.vue";

import { BoundingBox } from "@/models";

import { PVSystem, StoredPVSystem } from "@/models";

import GetColor from "@/utils/Colors";

interface TransformationEvent {
  target: L.Polyline;
}

Vue.component("l-map", LMap);
Vue.component("l-tile-layer", LTileLayer);
Vue.component("l-marker", LMarker);
Vue.component("l-control-scale", LControlScale);
Vue.component("l-control-layers", LControlLayers);
Vue.component("l-layer-group", LLayerGroup);
Vue.component("l-rectangle", LRectangle);
Vue.component("l-geo-json", LGeoJson);
Vue.component("static-area-rectangle", StaticAreaRectangle);
Vue.component("l-polyline", LPolyline);

@Component
export default class SystemMap extends Vue {
  @Prop() system!: PVSystem;
  @Prop({ default: () => [] }) systems!: Array<StoredPVSystem>;
  @Prop({ default: false }) editable!: boolean;
  @Prop() dc_capacity!: number;
  @Prop() all_systems!: Array<StoredPVSystem>;

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
  transmission!: Record<string, any>;
  transmissionLayers!: Array<any>;
  closestTransmission!: Record<string, any> | null;
  transmissionReady!: boolean;
  showTransmissionPath!: boolean;
  lastSelectedTransmission!: Record<string, any>;

  mapReady(): void {
    // @ts-expect-error accessing Leaflet API
    this.map = this.$refs.systemMap.mapObject;
    this.initialize();
  }
  selectTransmission(event: Record<string, any>): void {
    if (this.lastSelectedTransmission) {
      this.lastSelectedTransmission.setStyle({ color: "#444" });
    }
    // highlight transmission lines as they are clicked
    event.sourceTarget.setStyle({ color: "#8202ca" });
    this.lastSelectedTransmission = event.sourceTarget;
  }
  initialize(): void {
    this.draggable = true;
    if (this.editable) {
      this.scaling = true;
    } else {
      this.draggable = false;
      this.scaling = false;
    }
    if (typeof this.system !== "undefined") {
      if (this.system.boundary) {
        this.updateFromBoundingBox();
      }
    } else if (this.systems) {
      this.centerMap();
    }
    this.loadTransmission().then(() => {
      this.initialized = true;
    });
  }
  async loadTransmission(): Promise<void | Record<string, any>> {
    return fetch("/Electric_Power_Transmission_Lines.geojson").then(
      async (response: Record<string, any>) => {
        this.transmission = await response.json();
      }
    );
  }
  setTransmissionLayers(event: Record<string, any>): void {
    this.transmissionLayers = Object.values(event._layers);
    this.transmissionReady = true;
    this.findNearestTransmission();
  }

  findNearestTransmission(): void {
    if (this.transmissionReady) {
      if (this.system) {
        let closestTransmission = GeoUtil.closestLayer(
          this.map,
          this.transmissionLayers,
          this.centerCoords()
        );
        this.closestTransmission = closestTransmission;
      }
    }
  }

  data(): any {
    return {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      zoom: 11,
      center: this.centerCoords(),
      aspectX: 1,
      aspectY: 1,
      aspectInputX: 1,
      aspectInputY: 1,
      transmission: null,
      initialized: false,
      transmissionReady: false,
      closestTransmission: null,
      transmissionLayers: null,
      showTransmissionPath: false,
      lastSelectedTransmission: null,
    };
  }

  centerCoords(): L.LatLng {
    if (this.bounds) {
      return this.bounds.getCenter();
    } else {
      // approximately pheonix
      return L.latLng(33.4484, -112.074);
    }
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

  handleTransformation(transformEvent: TransformationEvent): void {
    // enforce area and emit parameters
    this.$emit(
      "bounds-updated",
      this.leafletBoundsToBoundingBox(transformEvent.target.getBounds())
    );
    this.findNearestTransmission();
  }

  @Watch("system")
  @Watch("systems", { deep: true })
  updateFromBoundingBox(): void {
    if (this.editable) {
      this.initAspectRatio();
    }
    this.centerMap();
    this.findNearestTransmission();
  }

  initAspectRatio(): void {
    if (this.bounds) {
      const xDist = this.bounds
        .getNorthWest()
        .distanceTo(this.bounds.getNorthEast());
      const yDist = this.bounds
        .getNorthWest()
        .distanceTo(this.bounds.getSouthWest());

      const xRatio = xDist / yDist;
      // Just set ratio so that one of the dimensions is 1, we aren't guarunteed
      // something that will reduce nicely.
      if (xRatio < 1) {
        this.aspectY = 1 / xRatio;
        this.aspectInputY = 1 / xRatio;
        this.aspectX = 1;
        this.aspectInputX = 1;
      } else {
        this.aspectX = xRatio;
        this.aspectInputX = xRatio;
        this.aspectY = 1;
        this.aspectInputY = 1;
      }
    }
  }
  get bounds(): L.LatLngBounds | null {
    if (this.system && this.system.boundary) {
      return this.boundingBoxToLeafletBounds(this.system.boundary);
    }
    return null;
  }
  getGroupBounds(): L.LatLngBounds {
    let all_bounds = [];
    for (let system of this.systems) {
      let bounds = this.boundingBoxToLeafletBounds(system.definition.boundary);
      all_bounds.push(bounds);
    }
    let north = Math.max(...all_bounds.map((b) => b.getNorth()));
    let east = Math.min(...all_bounds.map((b) => b.getEast()));
    let west = Math.max(...all_bounds.map((b) => b.getWest()));
    let south = Math.min(...all_bounds.map((b) => b.getSouth()));
    return L.latLngBounds(L.latLng(north, west), L.latLng(south, east));
  }
  @Watch("dc_capacity")
  adjustForCapacity(): void {
    if (this.bounds) {
      // increase the size of the system at the current center
      const currentCenter = this.bounds.getCenter();
      this.initializePolygon(currentCenter);
    }
  }

  areaFromCapacity(): number {
    // roughly 40MW/km^2  assumed
    return this.dc_capacity / 40;
  }

  initializePolygon(center: L.LatLng): void {
    // create a square based on provided area
    const area = this.areaFromCapacity();

    // determine length of one side of square from area
    const squareSideLength = Math.sqrt(area);
    const boundsOfArea = center.toBounds(squareSideLength * 1000);
    const reshaped = this.adjustBoundsToAspectRatio(boundsOfArea);
    this.$emit("bounds-updated", this.leafletBoundsToBoundingBox(reshaped));
  }
  adjustBoundsToAspectRatio(bounds: L.LatLngBounds): L.LatLngBounds {
    // naive scaling of lat/lon square bounds to aspect ratio
    if (this.aspectX != this.aspectY) {
      // aspect ratio -> ratio * a = b
      // > a * b = 1
      // > a * ratio * a = 1
      // > ratio * a^2 = 1
      // > a = sqrt(1/ratio)
      const xToYRatio = this.aspectX / this.aspectY;
      const yScale = Math.sqrt(1 / xToYRatio);
      const xScale = Math.sqrt(xToYRatio);

      const area = this.areaFromCapacity();
      const center = bounds.getCenter();
      // determine length of one side of square from area
      const squareSideLength = Math.sqrt(area) * 1000;
      const xRect = center.toBounds(squareSideLength * xScale);
      const yRect = center.toBounds(squareSideLength * yScale);
      return L.latLngBounds(
        [yRect.getNorth(), xRect.getWest()],
        [yRect.getSouth(), xRect.getEast()]
      );
    } else {
      return bounds;
    }
  }
  placeSystem(event: L.LeafletMouseEvent): void {
    if (this.bounds == null) {
      const center = event.latlng;
      this.initializePolygon(center);
      this.map.fitBounds(this.bounds!, { animate: true });
    }
    this.$emit("bounds-updated", this.leafletBoundsToBoundingBox(this.bounds!));
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

  centerMap(): void {
    if (this.system) {
      this.center = this.centerCoords();
    } else if (this.systems.length > 0) {
      this.map.fitBounds(this.getGroupBounds());
    }
  }

  emitSelection(system: StoredPVSystem): void {
    // Emit an event so parent components can update highlighting/selection
    this.$emit("new-selection", system);
  }
  reshape(): void {
    if (this.bounds != null) {
      const center = this.bounds.getCenter();
      this.initializePolygon(center);
    }
  }

  @Watch("aspectInputY")
  updateAspectY(newVal: number): void {
    if (
      // @ts-expect-error empty input returns empty string
      newVal != "" &&
      !isNaN(newVal) &&
      this.initialized &&
      !this.aspectInputsInvalid
    ) {
      this.aspectY = newVal;
      this.reshape();
    }
  }
  @Watch("aspectInputX")
  updateAspectX(newVal: number): void {
    if (
      // @ts-expect-error empty input returns empty string
      newVal != "" &&
      !isNaN(newVal) &&
      this.initialized &&
      !this.aspectInputsInvalid
    ) {
      this.aspectX = newVal;
      this.reshape();
    }
  }
  get aspectInputsInvalid(): boolean {
    return !(
      this.aspectInputX >= 1 &&
      this.aspectInputX <= 100 &&
      this.aspectInputY >= 1 &&
      this.aspectInputY <= 100
    );
  }
  getColor(index: number): string {
    return GetColor(index);
  }
  get transDistance(): number | null {
    if (this.closestTransmission) {
      let distKM =
        this.centerCoords().distanceTo(this.closestTransmission.latlng) / 1000;
      return parseFloat(distKM.toFixed(2));
    } else {
      return null;
    }
  }
  get transmissionPath(): Array<L.LatLng> | null {
    if (this.closestTransmission) {
      return [this.centerCoords(), this.closestTransmission.latlng];
    }
    return null;
  }
  get options(): Record<string, any> {
    return {
      onEachFeature: this.onEachFeature,
    };
  }
  onEachFeature(feature: Record<string, any>, layer: L.Layer): void {
    layer.bindPopup(`<div>
      <ul class="selected-transmission-attributes">
        <li>Owner: ${feature.properties.OWNER}</li>
        <li>Type: ${feature.properties.TYPE}</li>
        <li>Status: ${feature.properties.STATUS}</li>
        <li>Voltage: ${feature.properties.VOLTAGE} kV</li>
        <li>As of: ${feature.properties.VAL_DATE}</li>
      </ul>
    </div>`);
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
ul.selected-transmission-attributes {
  padding-left: 0;
}

/* Firefox */
input[type="number"] {
  -moz-appearance: textfield;
}
</style>
