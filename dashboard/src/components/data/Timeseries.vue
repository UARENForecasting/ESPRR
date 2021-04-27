<template>
  <div class="timeseries-plot">
    <h3>Timeseries</h3>
    Download:
    <button @click="downloadData('text/csv')">CSV</button>
    <button @click="downloadData('application/vnd.apache.arrow.file')">
      Apache Arrow
    </button>
    <br />
    <label>
      Variable:
      <select v-model="selected" @change="redraw">
        <option v-for="field in availableFields" :key="field">
          {{ field }}
        </option>
      </select>
    </label>
    <div :id="id"></div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import { getDisplayName } from "@/utils/DisplayNames";
import { Table } from "apache-arrow";
import { DateTime } from "luxon";
import Plotly from "plotly.js-basic-dist";

@Component
export default class TimeseriesPlot extends Vue {
  @Prop() timeseriesData!: Table;
  @Prop() title!: string;
  config = { responsive: true };
  selected!: string;

  // should update to be unique if we want multiple plots on a page
  id = "thePlot";

  data(): Record<string, any> {
    return {
      config: this.config,
      selected: this.selected,
    };
  }

  get yData(): Array<number> {
    return this.timeseriesData.getColumn(this.selected).toArray();
  }

  get xData(): Array<Date> {
    // Have to build times manually because calling .toArray() on the time
    // column results in a double length array with alternative 0 values
    // with apache-arrow 3.0.0
    let index = this.timeseriesData.getColumn("time");
    const dateTimes: Array<Date> = [];
    for (let i = 0; i < index.length; i++) {
      dateTimes.push(DateTime.fromMillis(index.get(i)).toJSDate());
    }
    return dateTimes;
  }

  get plotData(): Partial<Plotly.PlotData>[] {
    return [
      {
        x: this.xData,
        y: this.yData,
        type: "scatter",
      },
    ];
  }

  get availableFields(): Array<string> {
    return this.timeseriesData.schema.fields
      .map((x) => x.name)
      .filter((x) => x !== "time" && x !== "month");
  }

  get plotTitle(): string {
    return getDisplayName(this.selected);
  }

  get layout(): Record<string, any> {
    return {
      title: this.plotTitle,
      xaxis: {
        title: `Time`,
      },
      yaxis: {
        title: `${getDisplayName(this.selected)} (MW)`,
      },
    };
  }

  resetSelected(): void {
    this.selected = this.availableFields[0];
  }

  async mounted(): Promise<void> {
    this.resetSelected();
    await Plotly.react(this.id, this.plotData, this.layout, this.config);
  }

  @Watch("timeseriesData")
  changeData(): void {
    this.resetSelected();
    Plotly.react(this.id, this.plotData, this.layout, this.config);
  }

  redraw(): void {
    Plotly.react(this.id, this.plotData, this.layout, this.config);
  }

  downloadData(contentType: string): void {
    this.$emit("download-timeseries", contentType);
  }
}
</script>
