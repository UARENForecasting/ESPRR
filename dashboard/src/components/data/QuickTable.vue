<template>
  <div v-if="tableData" class="quick-summary">
    <h3>Summary ({{ units }})</h3>
    <table
      class="quick-table result-summary"
      :style="`--numCol: ` + (headers.length + 1)"
    >
      <thead>
        <tr>
          <th>Yearly Average</th>
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
import { getDisplayName } from "@/utils/DisplayNames";

@Component
export default class QuickTable extends Vue {
  @Prop() tableData!: Table;
  @Prop() asRampRate!: number;
  headers = ["10-min", "60-min"];

  get units(): string {
    if (this.asRampRate) {
      return "MW/min";
    } else {
      return "MW";
    }
  }

  scaleFactor(interval: string): number {
    if (this.asRampRate) {
      return Number(interval.split("-")[0]);
    } else {
      return 1;
    }
  }

  get tableRows(): Record<string, Record<string, number>> {
    const stats: Array<string> = Array.from(
      new Set(this.tableData.getColumn("statistic").toArray())
    );
    const rows: Record<string, Record<string, number>> = {};

    for (const stat of stats) {
      const statData = this.tableData.filter(
        predicate.col("statistic").eq(stat)
      );
      const niceStat = getDisplayName(stat);
      rows[niceStat] = {};
      for (const interval of this.headers) {
        // get and average the data over months
        const arr = Array.from(
          statData.filter(predicate.col("interval").eq(interval))
        );
        rows[niceStat][interval] = arr.reduce(
          (total, val) => total + val.value,
          0
        );
        rows[niceStat][interval] /= arr.length * this.scaleFactor(interval);
      }
    }
    return rows;
  }
}
</script>
<style>
table.quick-table {
  border-collapse: collapse;
  border: 1px solid black;
}
table.quick-table th,
table.quick-table tr td {
  padding: 0.5em;
  text-align: left;
  border: 1px solid black;
}
</style>
