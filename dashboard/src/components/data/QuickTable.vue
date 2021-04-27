<template>
  <div v-if="tableData" class="summary-table">
    <h3>Short Summary</h3>
    <table
      class="striped-table result-summary"
      :style="`--numCol: ` + (headers.length + 1)"
    >
      <thead>
        <tr>
          <th>Average</th>
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
  headers = ["10-min", "60-min"];

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
          (total, val) => total + val.value / arr.length,
          0
        );
      }
    }
    return rows;
  }
}
</script>
<style></style>
