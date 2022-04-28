import SystemGroups from "@/views/Groups.vue";
import { $auth } from "./mockauth";
import { listSystemGroups, deleteSystemGroup } from "@/api/systemGroups";

import { createLocalVue, mount } from "@vue/test-utils";
import VueRouter from "vue-router";
import router from "@/router";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");
jest.mock("@/api/systemGroups");

const localVue = createLocalVue();
localVue.use(VueRouter);

const mocks = { $auth };
const stubs = { "system-map": true };

describe("Test SystemGroups list", () => {
  beforeEach(() => {
    jest.resetModules();
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test load groups", async () => {
    const wrapper = mount(SystemGroups, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    expect(wrapper.findAll(".groups-table thead tr").length).toBe(1);

    //expect two group rows
    const siteRows = wrapper.findAll(".groups-table tbody tr");
    expect(siteRows.length).toBe(2);
    expect(siteRows.at(0).find("td").text()).toEqual("Test PV System Group");
  });
  it("test no groups", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    listSystemGroups.mockResolvedValueOnce([]);
    const wrapper = mount(SystemGroups, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();
    expect(wrapper.find(".groups-table").find("p").text()).toEqual(
      "No System Groups yet.\n        Create a new Group"
    );
  });
  it("test delete", async () => {
    const wrapper = mount(SystemGroups, {
      localVue,
      router,
      mocks,
      stubs,
    });
    await flushPromises();

    const groupRows = wrapper.findAll(".groups-table tbody tr");
    expect(groupRows.length).toBe(2);
    expect(wrapper.find("modal-block").exists()).toBe(false);
    wrapper.find("button.delete-group").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();

    expect(wrapper.find("modal-block").exists()).toBe(false);

    //expect one site row
    expect(wrapper.findAll(".groups-table tbody tr").length).toBe(1);
  });
  it("test delete without selection", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    listSystemGroups.mockResolvedValueOnce([]);
    const wrapper = mount(SystemGroups, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    // @ts-expect-error Vue instance method
    wrapper.vm.deleteGroup();

    await flushPromises();
    expect(deleteSystemGroup).not.toHaveBeenCalled();
  });
  it("test delete error", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    deleteSystemGroup.mockImplementationOnce(async () => {
      throw "error";
    });
    const wrapper = mount(SystemGroups, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    // @ts-expect-error Vue instance method
    wrapper.vm.deleteGroup();

    await flushPromises();
    // getSystemGroups is called after successful deletion to refresh
    // the systems list
    // @ts-expect-error accessing mock properties
    expect(listSystemGroups.mock.calls.length).toBe(1);
  });
});
