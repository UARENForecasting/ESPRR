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
      <reshape-rectangle
        v-if="sitePolygon"
        :draggable="editable"
        :scaling="editable"
        :rotation="false"
        :latLngs="sitePolygon"
        @transformed="handleTransformation"
      />
      <l-layer-group name="All Systems" layer-type="overlay" v-if="all_systems">
        <l-rectangle
          v-for="system of all_systems"
          :key="system.object_id"
          :bounds="createRectangle(system.definition.boundary)"
          @click="emitSelection(system)"
        >
        </l-rectangle>
      </l-layer-group>
    </l-map>
    <div class="map-prompt">
      <p v-if="editable && !bounds">
        Click on the map to place the system. The system will be represented by
        a square with an area corresponding to its DC capacity at a density of
        40 Megawatts per square kilometer.
      </p>
      <p v-if="editable && bounds">
        Click and drag to move the sytem's location.
      </p>
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
} from "vue2-leaflet";

import ReshapeRectangle from "@/components/leafletLayers/ReshapeRectangle.vue";

import { BoundingBox } from "@/models";

import { PVSystem, StoredPVSystem } from "@/models";

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
Vue.component("reshape-rectangle", ReshapeRectangle);
//Vue.component("v-path-transforms", Vue2LeafletPathTransform);

@Component
export default class SystemMap extends Vue {
  @Prop() system!: PVSystem;
  @Prop({ default: false }) editable!: boolean;
  @Prop() dc_capacity!: number;
  @Prop() all_systems!: Array<StoredPVSystem>;

  url!: string;
  attribution!: string;
  zoom!: number;
  center!: L.LatLng;
  draggable!: boolean;
  scaling!: boolean;
  bounds!: L.LatLngBounds;
  map!: L.Map;

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
    if (this.system.boundary) {
      this.updateFromBoundingBox();
    }
  }

  data(): any {
    return {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution:
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      zoom: 11,
      center: this.centerCoords(),
      bounds: null,
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
  }

  @Watch("system")
  updateFromBoundingBox(): void {
    this.bounds = this.boundingBoxToLeafletBounds(this.system.boundary);
    this.centerMap();
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

    this.bounds = center.toBounds(squareSideLength * 1000);
  }

  placeSystem(event: L.LeafletMouseEvent): void {
    if (!this.bounds) {
      const center = event.latlng;
      this.initializePolygon(center);
      this.map.fitBounds(this.bounds, { animate: true });
    }
    this.$emit("bounds-updated", this.leafletBoundsToBoundingBox(this.bounds));
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
    this.center = this.centerCoords();
  }

  emitSelection(system: StoredPVSystem): void {
    // Emit an event so parent components can update highlighting/selection
    this.$emit("new-selection", system);
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
</style>
