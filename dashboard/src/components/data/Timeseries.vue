84;0;0c
<template>
  <div class="timeseries-plot">
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
import { Table } from "apache-arrow";
import Plotly from "plotly.js-basic-dist";

@Component
export default class TimeseriesPlot extends Vue {
  @Prop() timeseriesData!: Table;
  @Prop() title!: string;
  config = { responsive: true };

  // should update to be unique if we want multiple plots on a page
  id = "thePlot";

  data() {
    return {
      config: this.config
    } 
  }
  get yData() {
    return this.timeseriesData.getColumn("ac").toArray();
  }
  get xData() {
    // Have to build times manually because calling .toArray() on the time
    // column results in a double length array with alternative 0 values
    // with apache-arrow 3.0.0
    let index = this.timeseriesData.getColumn("time");
    const dateTimes: Array<Date> = [];
    for (let i = 0; i < index.length; i++) {
      dateTimes.push(index.get(i));
    }
    return dateTimes;
  }
  get plotData(): Partial<Plotly.PlotData>[] {
    return [
      {
        x: this.xData,
        y: this.yData,
        type: "scatter"
      }
    ];
  }
  get availableFields() {
    return this.timeseriesData.schema.fields
      .map(x => x.name)
      .filter(x => x !== "time" && x !== "month");
  }
  get plotTitle() {
    return "AC Power (MW)";
  }
  get layout() {
    return {
      title: this.plotTitle,
      xaxis: {
        title: `Time`
      },
      yaxis: {
        title: "AC Power"
      }
    };
  }
  async mounted() {
    await Plotly.react(this.id, this.plotData, this.layout, this.config);
  }
  @Watch("timeseriesData")
  changeData() {
    Plotly.react(this.id, this.plotData, this.layout, this.config);
  }
  downloadData(contentType: string) {
    this.$emit("download-timeseries", contentType);
  }
}
</script>
