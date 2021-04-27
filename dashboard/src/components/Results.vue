<template>
  <div>
    <timeseries-plot
      @download-timeseries="downloadTimeseries"
      v-if="timeseries"
      :timeseriesData="timeseries"
    />
    <statistics-table
      @download-statistics="downloadStatistics"
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
import downloadFile from "@/utils/downloadFile";

Vue.component("timeseries-plot", TimeseriesPlot);
Vue.component("statistics-table", StatisticsTable);

@Component
export default class DataSetResults extends Vue {
  @Prop({ default: "NSRDB_2019" }) dataset!: string;
  @Prop() systemId!: string;

  status!: string;
  statistics!: Table | string | null;
  timeseries!: Table | string | null;

  created(): void {
    this.updateStatus();
  }
  data(): Record<string, any> {
    return {
      statistics: null,
      timeseries: null,
    };
  }
  async initialize(): void {
    if (this.status == "complete") {
      this.loadTimeseries();
      this.loadStatistics();
    } else {
      // TODO
      console.log(this.status);
    }
  }
  async updateStatus(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResult(token, this.systemId, this.dataset).then(
      (statusResponse: any) => {
        this.status = statusResponse.status;
        this.initialize();
      }
    );
  }
  async loadTimeseries(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultTimeseries(token, this.systemId, this.dataset).then(
      (timeseriesTable: Table | string) => {
        this.timeseries = timeseriesTable;
      }
    );
  }
  async loadStatistics(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultStatistics(
      token,
      this.systemId,
      this.dataset
      // @ts-expect-error Is Table
    ).then((statisticsTable: Table) => {
      this.statistics = statisticsTable;
    });
  }

  async downloadTimeseries(contentType: string): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    const contents: Blob = await SystemsAPI.fetchResultTimeseries(
      token,
      this.systemId,
      this.dataset,
      contentType
    ).then((response: Response): Promise<Blob> => response.blob());
    let filename: string;
    if (contentType == "text/csv") {
      filename = "timeseries.csv";
    } else {
      filename = "timeseries.arrow";
    }
    downloadFile(filename, contents);
  }

  async downloadStatistics(contentType: string): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    const contents: Blob = await SystemsAPI.fetchResultStatistics(
      token,
      this.systemId,
      this.dataset,
      contentType
    ).then((response: Response): Promise<Blob> => response.blob());
    let filename: string;
    if (contentType == "text/csv") {
      filename = "statistics.csv";
    } else {
      filename = "statistics.arrow";
    }
    downloadFile(filename, contents);
  }
}
</script>
