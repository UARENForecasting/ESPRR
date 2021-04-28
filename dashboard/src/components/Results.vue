<template>
  <div>
    <div v-if="errors" class="errors">
      Errors occurred during processing:
      <ul>
        <li v-for="error of errors" :key="error">
          {{ error }}
        </li>
      </ul>
    </div>
    <div v-if="status == 'queued'">
      Performance calculation is Queued and will be processed shortly.
    </div>
    <div v-if="status == 'statistics missing'">
      Result statistics are missing.
    </div>
    <div v-if="status == 'timeseries missing'">
      Result timeseries are missing.
    </div>
    <div v-if="status == 'running'">
      Performance calculation is running and will be ready soon.
    </div>
    <div class="results" v-if="status == 'complete'">
      <h2>Performance Results</h2>
      <hr />
      <timeseries-plot
        @download-timeseries="downloadTimeseries"
        v-if="timeseries"
        :timeseriesData="timeseries"
        :system="system"
        :dataset="dataset"
      />
      <statistics-table
        @download-statistics="downloadStatistics"
        v-if="statistics"
        :tableData="statistics"
      />
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Watch } from "vue-property-decorator";
import { StoredPVSystem } from "@/models";
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
  @Prop() system!: StoredPVSystem;

  status!: string | null;
  statistics!: Table | string | null;
  timeseries!: Table | string | null;
  timeout!: any;
  errors!: Record<string, any> | null;
  active!: boolean;

  created(): void {
    this.active = true;
    this.updateStatus();
  }

  destroyed(): void {
    // lifecycle hook to cleanup polling
    this.active = false;
    clearTimeout(this.timeout);
    this.status = null;
    this.errors = null;
  }

  data(): Record<string, any> {
    return {
      statistics: null,
      timeseries: null,
      status: null,
      errors: null,
      active: this.active,
    };
  }

  @Watch("system", { deep: true })
  loadNewSystemResults(): void {
    // Reload results if System ID changes.
    this.status = null;
    this.timeseries = null;
    this.statistics = null;
    this.updateStatus();
  }

  activated(): void {
    // hook for keep-alive lifecycle init
    this.active = true;
    this.updateStatus();
  }

  deactivated(): void {
    // hook for keep-alive lifecycle cleanup
    this.active = false;
    clearTimeout(this.timeout);
    this.status = null;
    this.errors = null;
  }

  async initialize(): Promise<void> {
    if (this.status) {
      if (this.status == "complete") {
        this.loadTimeseries();
        this.loadStatistics();
      } else if (this.status == "error") {
        return;
      } else {
        this.awaitResults();
      }
    } else {
      this.awaitResults();
    }
  }

  async awaitResults(): Promise<void> {
    // don't set timeout if the component has been deactivated
    if (this.active) {
      this.timeout = setTimeout(this.updateStatus, 1000);
    }
  }

  async updateStatus(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResult(token, this.system.object_id, this.dataset).then(
      (statusResponse: any) => {
        this.status = statusResponse.status;
        if (this.status == "error") {
          this.errors = statusResponse.error;
        }
        this.initialize();
      }
    );
  }

  async loadTimeseries(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultTimeseries(
      token,
      this.system.object_id,
      this.dataset
    ).then((timeseriesTable: Table | string) => {
      this.timeseries = timeseriesTable;
    });
  }

  async loadStatistics(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    SystemsAPI.getResultStatistics(
      token,
      this.system.object_id,
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
      this.system.object_id,
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
      this.system.object_id,
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
