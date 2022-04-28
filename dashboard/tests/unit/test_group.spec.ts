import SystemGroup from "@/views/Group.vue";

import { $auth } from "./mockauth";
import {
  getSystemGroup,
  getResult,
  deleteSystemGroup,
} from "@/api/systemGroups";

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
const stubs = {
  "system-map": true,
};

describe("Test System Group Details/Results page", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.useFakeTimers();
    if (
      // @ts-expect-error ts complains about history on VueRouter
      router.history.current.path !=
      "/system_group/04558a7c-c028-11ec-9d64-0242ac120002"
    ) {
      router.push({
        name: "Group Details",
        params: {
          groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
        },
      });
    }
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test Group With results", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
      },
    });

    await flushPromises();

    appTarget.remove();
  });
  it("Test delete system error", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
        dataset: "NSRDB_2019",
      },
    });

    // @ts-expect-error ts does not recognize mocked fn
    deleteSystemGroup.mockImplementationOnce(async () => {
      throw "error";
    });

    await flushPromises();
    expect(wrapper.find(".modal-block").exists()).toBe(false);
    wrapper.find("button.delete-group").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe(
      "/system_group/04558a7c-c028-11ec-9d64-0242ac120002"
    );
    appTarget.remove();
  });

  it("Test delete group", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);
    // @ts-expect-error ts does not recognize mocked fn
    deleteSystemGroup.mockImplementationOnce(async () => {
      return;
    });
    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
        dataset: "NSRDB_2019",
      },
    });

    await flushPromises();
    expect(wrapper.find(".modal-block").exists()).toBe(false);
    wrapper.find("button.delete-group").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe("/groups");
    appTarget.remove();
  });
  it("Test group dne", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-cc28-11ec-9d64-0242ac120002",
        dataset: "NSRDB_2019",
      },
    });

    await flushPromises();
    expect(wrapper.text()).toBe("The Group could not be found");
    appTarget.remove();
  });
  it("Test select year results", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
      },
    });

    await flushPromises();
    jest.runAllTimers();
    wrapper.find(".group-2019-results").trigger("click");
    await flushPromises();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe(
      "/system_group/04558a7c-c028-11ec-9d64-0242ac120002/NSRDB_2019"
    );
    appTarget.remove();
  });
  it("Test recompute results", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
      },
    });
    // @ts-expect-error mock function to set one status to a compute button
    getResult.mockImplementationOnce(async () => {
      throw "error";
    });
    await flushPromises();
    jest.runAllTimers();
    wrapper.find(".result-link.compute").trigger("click");
    await flushPromises();
    jest.runAllTimers();
    expect(wrapper.find(".result-link.compute").exists()).toBeFalsy;
    appTarget.remove();
  });
  it("Test test empty group", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);
    // @ts-expect-error mock group with no systems
    getSystemGroup.mockImplementationOnce(async () => {
      return {
        object_id: "04558a7c-c028-11ec-9d64-0242ac120002",
        object_type: "system_group",
        created_at: "2020-12-01T01:23:00+00:00",
        modified_at: "2020-12-01T01:23:00+00:00",
        definition: {
          name: "Test PV System Group",
          systems: [],
        },
      };
    });
    const wrapper = mount(SystemGroup, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7c-c028-11ec-9d64-0242ac120002",
      },
    });
    await flushPromises();
    expect(wrapper.find(".group-capacity").text()).toBe("Total Capacity: 0");
  });
});
