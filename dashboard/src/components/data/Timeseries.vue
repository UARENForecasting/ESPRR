<template>
  <div class="timeseries-plot">
    <h3>Timeseries</h3>
    Download:
    <button @click="downloadData('text/csv')">CSV</button>
    <button @click="downloadData('application/vnd.apache.arrow.file')">
      Apache Arrow
    </button>
    <br />
    <div :id="id"></div>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import { StoredPVSystem } from "@/models";
import { Table } from "apache-arrow";
import { DateTime } from "luxon";
import Plotly from "plotly.js-basic-dist";

@Component
export default class TimeseriesPlot extends Vue {
  @Prop() timeseriesData!: Table;
  @Prop() system!: StoredPVSystem;
  @Prop() dataset!: string;
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
        y: this.timeseriesData.getColumn("clearsky_ac_power").toArray(),
        name: "Clearsky AC Power",
        type: "scatter",
        showlegend: true,
      },
      {
        x: this.xData,
        y: this.timeseriesData.getColumn("ac_power").toArray(),
        name: "AC Power",
        type: "scatter",
        showlegend: true,
      },
    ];
  }

  get availableFields(): Array<string> {
    return this.timeseriesData.schema.fields
      .map((x) => x.name)
      .filter((x) => x !== "time" && x !== "month");
  }

  get plotTitle(): string {
    return `${this.dataset} ${this.system.definition.name} Performance`;
  }

  get layout(): Record<string, any> {
    return {
      title: this.plotTitle,
      xaxis: {
        title: `Time`,
      },
      yaxis: {
        title: "MW",
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
