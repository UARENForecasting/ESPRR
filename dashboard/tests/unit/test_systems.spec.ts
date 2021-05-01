import Systems from "@/views/Systems.vue";
import { $auth } from "./mockauth";
import { listSystems, deleteSystem } from "@/api/systems";

import { createLocalVue, mount } from "@vue/test-utils";
import VueRouter from "vue-router";
import router from "@/router";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");

const localVue = createLocalVue();
localVue.use(VueRouter);

const mocks = { $auth };
const stubs = { "system-map": true };

describe("Test Systems list", () => {
  beforeEach(() => {
    jest.resetModules();
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test load systems", async () => {
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    expect(wrapper.findAll("thead tr").length).toBe(1);

    //expect two site rows
    const siteRows = wrapper.findAll("tbody tr");
    expect(siteRows.length).toBe(2);
    expect(siteRows.at(0).find("td").text()).toEqual("Test PV System");
  });
  it("test no systems", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    listSystems.mockResolvedValueOnce([]);
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();
    expect(wrapper.find(".systems-table").find("p").text()).toEqual(
      "No Systems yet.\n        Create a new System"
    );
  });
  it("test delete", async () => {
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
      stubs,
    });
    await flushPromises();

    //expect two site rows
    const siteRows = wrapper.findAll("tbody tr");
    expect(siteRows.length).toBe(2);
    expect(wrapper.find("modal-block").exists()).toBe(false);
    wrapper.find("button.delete-system").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();

    expect(wrapper.find("modal-block").exists()).toBe(false);

    //expect one site row
    expect(wrapper.findAll("tbody tr").length).toBe(1);
  });
  it("test delete without selection", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    listSystems.mockResolvedValueOnce([]);
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    // @ts-expect-error Vue instance method
    wrapper.vm.deleteSystem();

    await flushPromises();
    expect(deleteSystem).not.toHaveBeenCalled();
  });
  it("test delete error", async () => {
    // @ts-expect-error ts does not recognize mocked fn
    deleteSystem.mockImplementationOnce(async () => {
      throw "error";
    });
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();

    // @ts-expect-error Vue instance method
    wrapper.vm.deleteSystem();

    await flushPromises();
    // getSystems is called after successful deletion to refresh
    // the systems list
    // @ts-expect-error accessing mock properties
    expect(listSystems.mock.calls.length).toBe(1);
  });
});
