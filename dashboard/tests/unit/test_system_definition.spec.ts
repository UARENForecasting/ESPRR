import SystemDefinition from "@/views/SystemDefinition.vue";
import SystemMap from "@/components/Map.vue";
import { $auth } from "./mockauth";
import {
  getSystem,
  createSystem,
  updateSystem,
  listSystems,
} from "@/api/systems";

import { createLocalVue, mount } from "@vue/test-utils";
import VueRouter from "vue-router";
import router from "@/router";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");

function errorFactory(error: string) {
  return {
    detail: [
      {
        loc: ["theError"],
        msg: error,
      },
    ],
  };
}

const localVue = createLocalVue();
localVue.use(VueRouter);

const mocks = { $auth };

describe("Test System Definition", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    // @ts-expect-error ts complains about history on VueRouter
    if (router.history.current.path != "/system/new") {
      router.push({ name: "New System" });
    }
  });
  it("Test new system", async () => {
    const wrapper = mount(SystemDefinition, {
      localVue,
      router,
      mocks,
    });
    await flushPromises();
    expect(wrapper.findAll("input").length).toBe(8);
    expect(wrapper.findComponent(SystemMap).exists()).toBe(true);
  });
  it("Test change tracking", async () => {
    const wrapper = mount(SystemDefinition, {
      localVue,
      router,
      mocks,
    });

    wrapper.vm.$data.definition.tracking.tilt = 12;
    expect(wrapper.vm.$data.definition.tracking).toEqual({
      tilt: 12,
      azimuth: 180,
    });

    // @ts-expect-error access vm
    wrapper.vm.changeTracking("singleAxis", "fixed");
    await flushPromises();

    expect(wrapper.vm.$data.definition.tracking).toEqual({
      axis_tilt: 12,
      axis_azimuth: 180,
      gcr: 0.4,
      backtracking: true,
    });

    // @ts-expect-error access vm
    wrapper.vm.changeTracking("fixed", "singleAxis");
    await flushPromises();

    expect(wrapper.vm.$data.definition.tracking).toEqual({
      tilt: 12,
      azimuth: 180,
    });

    // @ts-expect-error access vm
    wrapper.vm.changeTracking("fixed", "fixed");
    await flushPromises();

    expect(wrapper.vm.$data.definition.tracking).toEqual({
      tilt: 12,
      azimuth: 180,
    });
  });
  it("Test save system", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
    });
    // @ts-expect-error accessing vm method
    wrapper.vm.updateBounds({
      nw_corner: {
        latitude: 34.9,
        longitude: -112.9,
      },
      se_corner: {
        latitude: 33,
        longitude: -111,
      },
    });
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    expect(createSystem).toHaveBeenCalled();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe("/");
    appTarget.remove();
  });
  it("Test save system error", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    // @ts-expect-error mock object
    createSystem.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
    });
    // @ts-expect-error vm method
    wrapper.vm.updateBounds({
      nw_corner: {
        latitude: 34,
        longitude: -112,
      },
      se_corner: {
        latitude: 32,
        longitude: -110,
      },
    });
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();

    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe("/system/new");
    appTarget.remove();
  });
  it("Test update system fixed system", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
      },
    });
    await flushPromises();
    // @ts-expect-error value exists on html element
    expect(wrapper.find("input").element.value).toBe("Test PV System");
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    // @ts-expect-error ts complains about history on VueRouter
    expect(router.history.current.path).toBe("/");
    expect(updateSystem).toHaveBeenCalled();
    appTarget.remove();
  });
  it("Test update system single axis system", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9",
      },
    });
    await flushPromises();
    // @ts-expect-error value exists on html element
    expect(wrapper.find("input").element.value).toBe("Real PV System");
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    // @ts-expect-error ts complains about history on VueRouter
    expect(router.history.current.path).toBe("/");
    expect(updateSystem).toHaveBeenCalled();
    appTarget.remove();
  });
  it("Test update system 404", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    // @ts-expect-error mock object
    getSystem.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9",
      },
    });
    await flushPromises();
    expect(wrapper.find(".system-definition-form").text()).toBe(
      "Update System  The System could not be found."
    );
    appTarget.remove();
  });
  it("Test update system error", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    // @ts-expect-error mock object
    updateSystem.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    router.push({
      name: "Update System",
      params: { systemId: "6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9" },
    });
    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9",
      },
    });
    await flushPromises();

    wrapper.find("button[type='submit']").trigger("click");

    await flushPromises();
    expect(updateSystem).toHaveBeenCalled();
    // @ts-expect-error ts complains about history on VueRouter
    expect(router.history.current.path).toBe(
      "/system/6b61d9ac-2e89-11eb-be2b-4dc7a6bhe0a9"
    );
    appTarget.remove();
  });
  it("Test dc capacity null", async () => {
    const wrapper = mount(SystemDefinition, {
      localVue,
      router,
      mocks,
    });

    wrapper.vm.$data.definition.ac_capacity = null;
    // @ts-expect-error accessing vm getter
    expect(wrapper.vm.dcCapacity).toEqual(null);
  });
  it("Test dc capacity", async () => {
    const wrapper = mount(SystemDefinition, {
      localVue,
      router,
      mocks,
    });

    wrapper.vm.$data.definition.ac_capacity = 1;
    // @ts-expect-error accessing vm getter
    expect(wrapper.vm.dcCapacity).toEqual(1.2);
  });
  it("Test dc capacity", async () => {
    // @ts-expect-error mock object
    listSystems.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const wrapper = mount(SystemDefinition, {
      localVue,
      router,
      mocks,
    });

    await flushPromises();
    expect(wrapper.vm.$data.systems).toBe(null);
    expect(wrapper.find("ul.error-list").find("li").text()).toBe(
      "Error: Failed to load systems. Refresh the page to try again."
    );
  });
  it("Test update bounds", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
      },
    });
    await flushPromises();

    expect(wrapper.vm.$data.definition.boundary).toEqual({
      nw_corner: {
        latitude: 34.9,
        longitude: -112.9,
      },
      se_corner: {
        latitude: 33,
        longitude: -111,
      },
    });
    // @ts-expect-error vm method
    wrapper.vm.updateBounds({
      nw_corner: {
        latitude: 34,
        longitude: -112,
      },
      se_corner: {
        latitude: 32,
        longitude: -110,
      },
    });
    expect(wrapper.vm.$data.definition.boundary).toEqual({
      nw_corner: {
        latitude: 34,
        longitude: -112,
      },
      se_corner: {
        latitude: 32,
        longitude: -110,
      },
    });
    appTarget.remove();
  });
  it("Test save system error display", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);
    const errors = errorFactory("error");
    errors.detail.push({
      loc: ["__root__"],
      msg: "is bad",
    });
    // @ts-expect-error mock object
    createSystem.mockImplementationOnce(async () => {
      throw errors;
    });
    const wrapper = mount(SystemDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
    });
    // @ts-expect-error vm method
    wrapper.vm.updateBounds({
      nw_corner: {
        latitude: 34,
        longitude: -112,
      },
      se_corner: {
        latitude: 32,
        longitude: -110,
      },
    });
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    const htmlErrorList = wrapper.find("ul.error-list");
    const errorLis = htmlErrorList.findAll("li");
    expect(errorLis.at(0).text()).toBe("theError: error");
    expect(errorLis.at(1).text()).toBe("System: is bad");

    appTarget.remove();
  });
});
