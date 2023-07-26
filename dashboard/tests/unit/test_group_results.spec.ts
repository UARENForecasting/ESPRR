import Results from "@/components/GroupResults.vue";
import TimeseriesPlot from "@/components/data/Timeseries.vue";
import StatisticsTable from "@/components/data/StatisticsTable.vue";
import QuickTable from "@/components/data/QuickTable.vue";
import { $auth } from "./mockauth";
import { groups, tsTable, statisticsTable } from "@/api/__mocks__/systemGroups";
import {
  getResult,
  getResultTimeseries,
  getResultStatistics,
} from "@/api/systemGroups";

import { createLocalVue, mount } from "@vue/test-utils";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");
jest.mock("@/api/systemGroups");

const localVue = createLocalVue();

const mocks = { $auth };
const stubs = {
  "system-map": true,
};

describe("Test Group Results component", () => {
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
        group: groups[0],
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
        group: groups[0],
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
    getResult.mockImplementationOnce(async (token, gid, dataset) => {
      const data_status = {};
      // @ts-expect-error typescript is silly
      for (const system of groups[0].definition.systems) {
        // @ts-expect-error expression of type string is totally fine here
        data_status[system.object_id] = {
          system_id: system.object_id,
          status: "error",
          error: ["it's bad"],
          dataset: dataset,
        };
      }
      return {
        system_data_status: data_status,
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
        group: groups[0],
        dataset: "NSRDB_2019",
      },
    });

    await flushPromises();
    expect(wrapper.find(".errors").text()).toBe(
      "Errors occurred during processing of a system. Please see overview table."
    );
  });
  it("Test result status messages", async () => {
    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async (token, gid, dataset) => {
      const data_status = {};
      // @ts-expect-error typescript is silly
      for (const system of groups[0].definition.systems) {
        // @ts-expect-error expression of type string is totally fine here
        data_status[system.object_id] = {
          system_id: system.object_id,
          status: "queued",
          dataset: dataset,
        };
      }
      return {
        system_data_status: data_status,
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
        group: groups[0],
        dataset: "NSRDB_2019",
      },
    });
    await flushPromises();
    expect(wrapper.text()).toBe(
      "Performance calculation is queued and will be processed shortly."
    );

    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async (token, gid, dataset) => {
      const data_status = {};
      // @ts-expect-error typescript is silly
      for (const system of groups[0].definition.systems) {
        // @ts-expect-error expression of type string is totally fine here
        data_status[system.object_id] = {
          system_id: system.object_id,
          status: "running",
          dataset: dataset,
        };
      }
      return {
        system_data_status: data_status,
      };
    });
    jest.runAllTimers();
    await flushPromises();
    expect(wrapper.text()).toBe(
      "Performance calculation is running and will be ready soon."
    );

    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async (token, gid, dataset) => {
      const data_status = {};
      // @ts-expect-error typescript is silly
      for (const system of groups[0].definition.systems) {
        // @ts-expect-error expression of type string is totally fine here
        data_status[system.object_id] = {
          system_id: system.object_id,
          status: "timeseries missing",
          dataset: dataset,
        };
      }
      return {
        system_data_status: data_status,
      };
    });
    jest.runAllTimers();
    await flushPromises();

    expect(wrapper.text()).toContain(
      "Results could not be computed for this group"
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
        group: groups[0],
      },
    });

    await flushPromises();
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
        group: groups[0],
        dataset: "NSRDB_2017",
      },
    });

    await flushPromises();
    const warning = wrapper.find(".no-dataset-warning");
    expect(warning.text()).toBe(
      "You are trying to access an invalid dataset. Valid datasets are\n" +
        "    NSRDB_2018, NSRDB_2019, NSRDB_2020, NSRDB_2021."
    );
  });
  it("Test results dne", async () => {
    // @ts-expect-error mocked fn
    getResult.mockImplementationOnce(async () => {
      throw "error";
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
        group: groups[0],
      },
    });

    await flushPromises();
    const warning = wrapper.find("div.alert");
    expect(warning.text()).toContain("Results could not be computed");
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
        group: groups[0],
      },
    });
    await flushPromises();

    wrapper.setProps({
      dataset: "NSRDB_2018",
      group: Object.assign({}, groups[0]),
    });
    // @ts-expect-error manually calling watch function
    await wrapper.vm.reloadDataset();
    jest.runAllTimers();
    await flushPromises();

    // @ts-expect-error mocked function has .mock property
    expect(getResult.mock.calls[1][2]).toBe("NSRDB_2018");
  });
  it("Test data missing", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    // @ts-expect-error typescript doesn't know this is mocked
    getResultTimeseries.mockImplementationOnce(async () => {
      throw "error";
    });
    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        group: groups[0],
      },
    });
    await flushPromises();
    expect(wrapper.find("div.alert").text()).toContain("Results could not");
  });
  it("Test stats missing", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    // @ts-expect-error typescript doesn't know this is mocked
    getResultStatistics.mockImplementationOnce(async () => {
      throw "error";
    });
    const wrapper = mount(Results, {
      attachTo: "#app",
      localVue,
      mocks,
      stubs,
      propsData: {
        group: groups[0],
      },
    });
    await flushPromises();
    expect(wrapper.find("div.alert").text()).toContain("Results could not");
  });
});
