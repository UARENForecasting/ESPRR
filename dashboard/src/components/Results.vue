<template>
  <div>
    <timeseries-plot
      @download-timeseries="downloadData"
      v-if="timeseries"
      :timeseriesData="timeseries"
      />
    <statistics-table
      v-if="statistics"
      :tableData="statistics"
    />
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop } from "vue-property-decorator";
import TimeseriesPlot from "@/components/data/Timeseries.vue";
import StatisticsTable from "@/components/data/StatisticsTable.vue";


import * as SystemsAPI from "@/api/systems";
import { Table } from "apache-arrow";
import downloadFile from "@/utillsdownloadFile";

Vue.component("timeseries-plot", TimeseriesPlot);
Vue.component("statistics-table", StatisticsTable);

@Component
export default class DataSetResults extends Vue {
  @Prop({default: "NSRDB_2019"}) dataset!: string;
  @Prop() systemId!: string;

  status!: string;
  statistics!: Table | null;
  timeseries!: Table | string | null;

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
      console.log(this.status);
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
      this.dataset,
    ).then((timeseriesTable: Table|string) => {
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

  async downloadTimeseries(dataType: string, contentType: string) {
    const token = await this.$auath.getTokenSilently();
    const contents = await SystemsApi.fetchResultTimeseries(
      token, this.systemId, this.dataset, contentType
    ).then((response: Response) => response.blob())
    downloadFile("file.arrow", contents);

  }

  async downloadStatistics(contentType: string) {
    const token = await this.$auath.getTokenSilently();
    contents = await SystemsApi.fetchResultStatistics(
      token, this.systemId, this.dataset, contentType
    ).then((response: Response) => response.blob())
    downloadFile("file.csv", contents);
  }
}
</script>
