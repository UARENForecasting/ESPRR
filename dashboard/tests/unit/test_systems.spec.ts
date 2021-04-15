import Systems from "@/views/Systems.vue";
import { $auth } from "./mockauth";
import { listSystems } from "@/api/systems";

import { createLocalVue, mount } from "@vue/test-utils";
import VueRouter from "vue-router";
import router from "@/router";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");

const localVue = createLocalVue();
localVue.use(VueRouter);

const mocks = { $auth };

describe("Test Systems list", () => {
  beforeEach(() => {
    jest.resetModules();
  });
  it("Test load systems", async () => {
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
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
    });

    await flushPromises();
    expect(wrapper.find(".systems-table").find("p").text()).toEqual(
      "No Systems yet. Create a new system."
    );
  });
  it("test delete", async () => {
    const wrapper = mount(Systems, {
      localVue,
      router,
      mocks,
    });
    await flushPromises();

    //expect two site rows
    const siteRows = wrapper.findAll("tbody tr");
    expect(siteRows.length).toBe(2);

    wrapper.find("button.delete-system").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();
    //expect one site row
    expect(wrapper.findAll("tbody tr").length).toBe(1);
  });
});
