<template>
  <div class="l-wrapper">
    <p v-if="!capacity">Enter a capacity to map system.</p>
    <l-map
      ref="systemMap"
      :zoom="zoom"
      :center="center"
      @ready="mapReady"
      @click="placeSystem"
    >
      <l-tile-layer :url="url" :attribution="attribution"> </l-tile-layer>
      <l-control-scale
        position="bottomleft"
        :imperial="false"
        :metric="true"
      ></l-control-scale>
      <v-path-transforms
        v-if="sitePolygon"
        :latLngs="sitePolygon"
        :draggable="draggable"
        :rotation="false"
        :scaling="scaling"
        @transformed="handleTransformation"
      >
        <l-popup v-if="!editable">Wow</l-popup>
      </v-path-transforms>
    </l-map>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";

import L from "leaflet";
import { LMap, LTileLayer, LMarker, LPopup, LControlScale } from "vue2-leaflet";
import Vue2LeafletPathTransform from "vue2-leaflet-path-transform";
import { BoundingBox } from "@/models";

Vue.component("l-map", LMap);
Vue.component("l-tile-layer", LTileLayer);
Vue.component("l-marker", LMarker);
Vue.component("l-control-scale", LControlScale);
Vue.component("l-popup", LPopup);
Vue.component("v-path-transforms", Vue2LeafletPathTransform);

@Component
export default class SystemMap extends Vue {
  @Prop() systemBounds!: BoundingBox;
  @Prop({ default: false }) editable!: boolean;
  @Prop() capacity!: number;

  url!: string;
  attribution!: string;
  zoom!: number;
  center!: L.LatLng;
  draggable!: boolean;
  scaling!: boolean;
  bounds!: L.LatLngBounds;
  map!: L.Map;

  created(): void {
    if (this.editable) {
      this.draggable = true;
      this.scaling = true;
    } else {
      this.draggable = false;
      this.scaling = false;
    }
    if (this.systemBounds) {
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

  mapReady(): void {
    // @ts-expect-error accessing Leaflet API
    this.map = this.$refs.systemMap.mapObject;
  }

  handleTransformation(transformEvent: any): void {
    // enforce area and emit parameters
    console.log(transformEvent);
    this.$emit(
      "bounds-updated",
      this.leafletBoundsToBoundingBox(transformEvent.target.getBounds())
    );
  }

  @Watch("systemBounds")
  updateFromBoundingBox(): void {
    this.bounds = this.boundingBoxToLeafletBounds(this.systemBounds);
    this.centerMap();
  }

  @Watch("capacity")
  adjustForCapacity(): void {
    if (this.bounds) {
      // increase the size of the system at the current center
      const currentCenter = this.bounds.getCenter();
      this.initializePolygon(currentCenter);
    }
  }

  areaFromCapacity(): number {
    // roughly 36MW/km^2 assumed
    return this.capacity / 36;
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
  centerMap(): void {
    this.center = this.centerCoords();
  }
}
</script>
<style scoped>
.l-wrapper {
  width: 100%;
  height: 100%;
}
</style>
