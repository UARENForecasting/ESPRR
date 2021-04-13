<template>
  <l-map
    :zoom="zoom"
    :center="center"
    
    >
    <l-tile-layer
      :url="url"
      :attribution="attribution"
      >
    </l-tile-layer>
  </l-map>
</template>
<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

import L from "leaflet";
import { latLng } from "leaflet";
import { LMap, LTileLayer, LMarker } from "vue2-leaflet";

Vue.component('l-map', LMap);
Vue.component('l-tile-layer', LTileLayer);
Vue.component('l-marker', LMarker);

@Component
export default class MappyMap extends Vue {
  data() {
    return {
      url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: 
        '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
      zoom: 13,
      center: latLng(32.2319, -110.9501)
    }
  }
}
</script>
