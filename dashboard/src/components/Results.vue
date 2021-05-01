<template>
  <div>
    <div v-if="errors" class="errors">
      Errors occurred during processing:
      <ul>
        <li v-for="error of errors" :key="error">
          {{ error }}
        </li>
      </ul>
      <br />
      <button @click="recompute">Recalculate</button>
    </div>
    <div v-if="status == 'queued'">
      Performance calculation is queued and will be processed shortly.
    </div>
    <div v-if="status == 'running'">
      Performance calculation is running and will be ready soon.
    </div>
    <div
      class="results"
      v-if="
        (status == 'complete') |
          (status == 'statistics missing') |
          (status == 'timeseries missing')
      "
    >
      <h2>Performance Results</h2>
      <hr />
      <div class="alert" v-if="status == 'timeseries missing'">
        Result timeseries are missing.
        <button @click="recompute">Recalculate</button>
      </div>
      <div class="alert" v-if="status == 'statistics missing'">
        Result statistics are missing.
        <button @click="recompute">Recalculate</button>
      </div>
      <div class="flex-container">
        <div class="description-flex">
          <h3>Data Processing</h3>
          <p>
            Irradiance, temperature, and wind data from the
            {{ this.prettyDataset }} dataset were extracted for all gridpoints
            contained within or intersecting the system bounding box. The data
            were then processed using a PV model with parameters defined above
            to generate the expected power timeseries. The PV model is based on
            the NREL PVWatts model and accounts for angle of incidence and
            temperature losses. Ramps were calculated at various intervals by
            resampling this timeseries and calculating the derivatives. These
            ramps were binned by month to determine the stress-case up and down
            ramps. The typical sunrise and sunset ramps were calculated in a
            similar fashion using the expected clearsky timeseries.
          </p>
        </div>
        <div class="quick-table-flex">
          <quick-table
            v-if="statistics"
            :tableData="statistics"
            :asRampRate="asRampRate"
          />
        </div>
        <div class="option-flex">
          <h3>Options</h3>
          <div class="stat-option">
            <label>
              <b>Display statistics as:</b>
              <br />
              <label
                title="Present statistics in terms of absolute power ramps"
              >
                <input
                  type="radio"
                  id="absolute"
                  name="units"
                  value="0"
                  v-model.number="asRampRate"
                />
                Absolute Ramps (MW)
              </label>
              <br />
              <label title="Present statistics in terms of MW/min ramp rates">
                <input
                  type="radio"
                  id="rate"
                  name="units"
                  value="1"
                  v-model.number="asRampRate"
                />
                Ramp Rates (MW/min)
              </label>
            </label>
          </div>
          <button @click="recompute">Recalculate</button>
        </div>
        <div class="download-flex">
          <h3>Downloads</h3>
          <div>
            <strong>Timeseries: </strong>
            <button @click="downloadTimeseries('text/csv')">CSV</button>
            <button
              @click="downloadTimeseries('application/vnd.apache.arrow.file')"
            >
              Apache Arrow
            </button>
          </div>
          <div>
            <strong>Statistics: </strong>
            <button @click="downloadStatistics('text/csv')">CSV</button>
            <button
              @click="downloadStatistics('application/vnd.apache.arrow.file')"
            >
              Apache Arrow
            </button>
          </div>
          <p>
            Downloaded statistics are in terms of absolute ramps with units of
            MW. <a href="https://arrow.apache.org">Apache Arrow</a> is an
            optimized binary format that can quickly be read with pandas or R.
            In python, use <code>pandas.read_feather</code> to quickly read the
            data into a DataFrame.
          </p>
        </div>
      </div>
      <timeseries-plot
        v-if="timeseries"
        :timeseriesData="timeseries"
        :system="system"
        :dataset="dataset"
      />
      <statistics-table
        v-if="statistics"
        :tableData="statistics"
        :asRampRate="asRampRate"
      />
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop } from "vue-property-decorator";
import { StoredPVSystem } from "@/models";
import TimeseriesPlot from "@/components/data/Timeseries.vue";
import StatisticsTable from "@/components/data/StatisticsTable.vue";
import QuickTable from "@/components/data/QuickTable.vue";

import * as SystemsAPI from "@/api/systems";
import { Table } from "apache-arrow";
import downloadFile from "@/utils/downloadFile";
import { getDisplayName } from "@/utils/DisplayNames";

Vue.component("timeseries-plot", TimeseriesPlot);
Vue.component("statistics-table", StatisticsTable);
Vue.component("quick-table", QuickTable);

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
  asRampRate!: number;

  created(): void {
    this.active = true;
    this.updateStatus();
    this.asRampRate = 0;
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
      timeout: null,
      asRampRate: null,
    };
  }

  get prettyDataset(): string {
    return getDisplayName(this.dataset);
  }

  async initialize(): Promise<void> {
    if (this.status == "complete") {
      this.loadTimeseries();
      this.loadStatistics();
    } else if (this.status == "timeseries missing") {
      this.loadStatistics();
    } else if (this.status == "statistics missing") {
      this.loadTimeseries();
    } else if (this.status == "error") {
      return;
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

  /* istanbul ignore next */
  async downloadTimeseries(contentType: string): Promise<void> {
    if (!this.timeseries) {
      return;
    }
    const token = await this.$auth.getTokenSilently();
    const contents: Blob = await SystemsAPI.fetchResultTimeseries(
      token,
      this.system.object_id,
      this.dataset,
      contentType
    ).then((response: Response): Promise<Blob> => response.blob());
    let filename = `${this.system.definition.name.replace(/ /g, "_")}_${
      this.dataset
    }_timeseries`;
    if (contentType == "text/csv") {
      filename += ".csv";
    } else {
      filename += ".arrow";
    }
    downloadFile(filename, contents);
  }

  /* istanbul ignore next */
  async downloadStatistics(contentType: string): Promise<void> {
    if (!this.statistics) {
      return;
    }
    const token = await this.$auth.getTokenSilently();
    const contents: Blob = await SystemsAPI.fetchResultStatistics(
      token,
      this.system.object_id,
      this.dataset,
      contentType
    ).then((response: Response): Promise<Blob> => response.blob());
    let filename = `${this.system.definition.name.replace(/ /g, "_")}_${
      this.dataset
    }_statistics`;
    if (contentType == "text/csv") {
      filename += ".csv";
    } else {
      filename += ".arrow";
    }
    downloadFile(filename, contents);
  }

  /* istanbul ignore next */
  async recompute(): Promise<void> {
    const token = await this.$auth.getTokenSilently();
    await SystemsAPI.startProcessing(
      token,
      this.system.object_id,
      this.dataset
    );
    window.location.reload();
  }
}
</script>
<style scoped>
.flex-container {
  display: flex;
  flex-direction: row;
  max-width: 1400px;
  margin-bottom: 3vh;
}

@media (max-width: 800px) {
  .flex-container {
    flex-direction: column;
  }
}
.description-flex {
  margin-left: 1vw;
  margin-right: 1.5vw;
  flex: 20%;
}
.quick-table-flex {
  margin: 0 0.5vw;
  flex: 25%;
}
.option-flex {
  margin: 0 0.5vw;
  flex: 15%;
}
.download-flex {
  margin: 0 0.5vw;
  flex: 20%;
}
.stat-option {
  margin-bottom: 1em;
}
.summary-table {
  margin: 1vh 1vw 3vh 1vw;
}
</style>
