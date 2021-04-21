<template>
</template>
<script>
import { Vue, Component, Prop } from "vue-property<template>

@Component
export default class DataSetResults extends Vue {
  @Prop({default: "NSRDB_2019"}) dataset!: string;
  @Prop() SystemId!: string;

  status!: string;
  

  updateStatus(): void {
    this.status = "complete";
  }
}
</script>
