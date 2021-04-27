<template>
  <div v-if="tableData" class="summary-table">
    <h3>Statistics</h3>
    Download:
    <button id="download-statistics-csv" @click="downloadData('text/csv')">
      CSV
    </button>
    <button
      id="download-statistics-arrow"
      @click="downloadData('application/vnd.apache.arrow.file')"
    >
      Apache Arrow
    </button>
    <br />
    <label>
      <b>Interval</b>
      <select v-model="selectedInterval">
        <option v-for="interval of availableIntervals" :key="interval">
          {{ interval }}
        </option>
      </select>
    </label>
    <label>
      <b>Units</b>
      <label>
        Absolute Ramps (MW)
        <input
          type="radio"
          id="absolute"
          name="units"
          value="false"
          v-model="asRampRate"
        />
      </label>
      <label>
        Ramp Rates (MW/min)
        <input
          type="radio"
          id="rate"
          name="units"
          value="true"
          v-model="asRampRate"
        />
      </label>
    </label>
    <table
      class="striped-table result-summary"
      :style="`--numCol: ` + (headers.length + 1)"
    >
      <thead>
        <tr>
          <th>Month</th>
          <th v-for="(header, i) of headers" :key="i">
            {{ header }}
          </th>
        </tr>

        <tr />
      </thead>
      <tbody>
        <tr v-for="(values, stat) in tableRows" :key="stat">
          <td>{{ stat }}</td>
          <td v-for="(col, j) of headers" :key="j">
            {{ values[col].toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop } from "vue-property-decorator";
import { Table, predicate } from "apache-arrow";

@Component
export default class StatisticsTable extends Vue {
  @Prop() tableData!: Table;
  asRampRate!: string;
  selectedInterval!: string;

  created(): void {
    this.selectedInterval = this.availableIntervals[0];
    this.asRampRate = "false";
  }
  data(): Record<string, any> {
    return {
      selectedInterval: this.selectedInterval,
      asRampRate: this.asRampRate,
    };
  }

  get headers(): Array<string | number> {
    return Array.from(
      new Set(this.filteredTable.getColumn("statistic").toArray())
    );
  }

  get filteredTable(): Table {
    return this.tableData.filter(
      predicate.col("interval").eq(this.selectedInterval)
    );
  }

  get scaleFactor(): number {
    if (this.asRampRate === "true") {
      return Number(this.selectedInterval.split("-")[0]);
    } else {
      return 1;
    }
  }

  get tableRows(): Record<string, Record<string, number>> {
    const rows: Record<string, Record<string, number>> = {};
    for (const row of this.filteredTable) {
      if (!(row["month"] in rows)) {
        rows[row["month"]] = {};
      }
      rows[row["month"]][row["statistic"]] = row.value / this.scaleFactor;
    }
    return rows;
  }

  get availableIntervals(): Array<string> {
    return Array.from(new Set(this.tableData.getColumn("interval")));
  }

  downloadData(contentType: string): void {
    /* istanbul ignore next */
    this.$emit("download-statistics", contentType);
  }
}
</script>
<style></style>
