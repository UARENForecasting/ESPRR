<template>
  <div class="systems" v-if="$auth.isAuthenticated">
    <ul>
      <li v-for="system of systems" :key="system.object_id">
        {{ system.name }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";

@Component
export default class Systems extends Vue {
  systems!: Record<string, any>[];

  data() {
    return {
      systems: [
        {
          name: "System 1",
        },
        {
          name: "System 2",
        },
      ],
    };
  }
}
</script>
