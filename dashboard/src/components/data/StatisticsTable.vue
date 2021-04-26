<template>
  <div v-if="tableData" class="summary-table">
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
          <td> {{ stat }}</td>
          <td v-for="(col, j) of headers" :key="j">
            {{ values[col].toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import { Table, predicate } from "apache-arrow";

// collection of anonymous functions for displaying values
const formatFuncs = {
  actual_energy: (x: number) => x.toFixed(0),
  weather_adjusted_energy: (x: number) => x.toFixed(0),
  modeled_energy: (x: number) => x.toFixed(0),
  difference: (x: number) => x.toFixed(0),
  ratio: (x: number) => (x * 100).toFixed(1),
  plane_of_array_insolation: (x: number) => x.toFixed(0),
  effective_insolation: (x: number) => x.toFixed(0),
  total_energy: (x: number) => x.toFixed(0),
  average_daytime_cell_temperature: (x: number) => x.toFixed(0)
};

@Component
export default class StatisticsTable extends Vue {
  @Prop() tableData!: Record<string, Table>;

  data() {
    return {
      units: {},
      unitOptions: {}
    };
  }
  
  get headers() {
    return Array.from(new Set(this.filteredTable.getColumn("statistic").toArray()));
  }

  get filteredTable(): Table {
    return this.tableData.filter(
      predicate.col("interval").eq("5-min")
    );
  }

  get tableRows() {
    const rows: Record<string, Record<string,number>> = {};
    for (const row of this.filteredTable) {
      if(!(row["month"] in rows)) {
        rows[row["month"]] = {};
      }
      rows[row["month"]][row["statistic"]] = row.value;
    }
    return rows;
  }
}
</script>
<style>
</style>
