import Results from "@/components/Results.vue";
import TimeseriesPlot from "@/components/data/Timeseries.vue";
import StatisticsTable from "@/components/data/StatisticsTable.vue";
import QuickTable from "@/components/data/QuickTable.vue";
import { $auth } from "./mockauth";
import { systems, tsTable, statisticsTable } from "@/api/__mocks__/systems";
import { getResult, startProcessing } from "@/api/systems";

import { createLocalVue, mount } from "@vue/test-utils";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");

const localVue = createLocalVue();

const mocks = { $auth };
const stubs = {
  "system-map": true,
};

describe("Test Results component", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.useFakeTimers();
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test results", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    const plot = wrapper.findComponent(TimeseriesPlot);
    const statTable = wrapper.findComponent(StatisticsTable);
    const summaryTable = wrapper.findComponent(QuickTable);
    expect(plot.exists()).toBe(true);
    expect(plot.props("timeseriesData")).toEqual(tsTable);
    expect(statTable.exists()).toBe(true);
    expect(statTable.props("tableData")).toEqual(statisticsTable);
    expect(summaryTable.exists()).toBe(true);
    expect(summaryTable.props("tableData")).toEqual(statisticsTable);
  });
  it("Test results ramp switch", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    const statTable = wrapper.findComponent(StatisticsTable);
    const summaryTable = wrapper.findComponent(QuickTable);
    expect(statTable.props("asRampRate")).toEqual(0);
    expect(summaryTable.props("asRampRate")).toEqual(0);

    const rampRadio = wrapper.find("#rate");
    rampRadio.trigger("click");
    await flushPromises();

    expect(statTable.props("asRampRate")).toEqual(1);
    expect(summaryTable.props("asRampRate")).toEqual(1);
  });
  it("Test result status error", async () => {
    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      return {
        status: "error",
        error: ["it's bad"],
      };
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    expect(wrapper.find(".errors").text()).toBe(
      "Errors occurred during processing:\n    \n        it's bad\n        Recalculate"
    );
  });
  it("Test result status messages", async () => {
    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      return {
        status: "queued",
      };
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    expect(wrapper.text()).toBe(
      "Performance calculation is queued and will be processed shortly."
    );

    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      return {
        status: "running",
      };
    });
    jest.runAllTimers();
    await flushPromises();
    expect(wrapper.text()).toBe(
      "Performance calculation is running and will be ready soon."
    );

    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      return {
        status: "statistics missing",
      };
    });
    jest.runAllTimers();
    await flushPromises();
    expect(wrapper.find(".alert").text()).toBe(
      "Result statistics are missing.\n      Recalculate"
    );

    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      return {
        status: "timeseries missing",
      };
    });
    // @ts-expect-error instance method
    wrapper.vm.awaitResults();
    jest.runAllTimers();
    await flushPromises();
    expect(wrapper.find(".alert").text()).toBe(
      "Result timeseries are missing.\n      Recalculate"
    );
  });
  it("Test results destroyed method", async () => {
    // @ts-expect-error mock queued state so timeout will be set
    getResult.mockImplementationOnce(async () => {
      return {
        status: "queued",
      };
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    expect(wrapper.vm.$data.timeout).toBeTruthy();
    wrapper.destroy();

    // @ts-expect-error mock fn
    expect(getResult.mock.calls.length).toBe(1);

    // @ts-expect-error instance method
    wrapper.vm.awaitResults();
    jest.runAllTimers();
    await flushPromises();

    // no more calls are made, polling has stopped
    // @ts-expect-error mock fn
    expect(getResult.mock.calls.length).toBe(1);

    expect(wrapper.vm.$data.active).toBe(false);
    expect(wrapper.vm.$data.status).toBe(null);
    expect(wrapper.vm.$data.errors).toBe(null);
  });
  it("Test results bad dataset", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
        dataset: "NSRDB_2017",
      },
    });

    await flushPromises();
    const warning = wrapper.find(".no-dataset-warning");
    expect(warning.text()).toBe(
      "You are trying to access an invalid dataset. Valid datasets are\n" +
        "    NSRDB_2018, NSRDB_2019, NSRDB_2020."
    );
  });
  it("Test result dne", async () => {
    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      throw "error";
    });
    // @ts-expect-error mocked fn
    startProcessing.mockImplementationOnce(async () => {
      return;
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        system: systems[0],
      },
    });

    await flushPromises();
    expect(startProcessing).toHaveBeenCalled();
  });
});
