<template>
  <div>
    <timeseries-plot
      v-if="timeseries"
      :timeseriesData="timeseries"
      />
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop } from "vue-property-decorator";
import TimeseriesPlot from "@/components/data/Timeseries.vue";

import * as SystemsAPI from "@/api/systems";
import { Table } from "apache-arrow";

Vue.component("timeseries-plot", TimeseriesPlot);

@Component
export default class DataSetResults extends Vue {
  @Prop({default: "NSRDB_2019"}) dataset!: string;
  @Prop() systemId!: string;

  status!: string;
  statistics!: Table | null;
  timeseries!: Table | null;

  created() {
    this.updateStatus();
  }
  data() {
    return {
      statistics: null,
      timeseries: null
    }
  }
  async initialize() {
    if (this.status == "complete") {
      this.loadTimeseries();
      this.loadStatistics();
    } else {
      console.log("UHHH");
    }
  }
  async updateStatus(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    const resultStatus = await SystemsAPI.getResult(
      token,
      this.systemId,
      this.dataset
    ).then((statusResponse: any) => {
      this.status = statusResponse.status;
      this.initialize();
    });
  }
  async loadTimeseries() {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultTimeseries(
      token,
      this.systemId,
      this.dataset   
    ).then((timeseriesTable: Table) => {
      this.timeseries = timeseriesTable;
    });
  }
  async loadStatistics() {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultStatistics(
      token,
      this.systemId,
      this.dataset   
    ).then((statisticsTable: Table) => {
      this.statistics = statisticsTable;
    });
  }
}
</script>
