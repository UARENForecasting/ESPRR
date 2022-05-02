import GroupDefinition from "@/views/GroupDefinition.vue";

import { $auth } from "./mockauth";
import { listSystems } from "@/api/systems";
import {
  createSystemGroup,
  updateSystemGroup,
  removeSystemFromSystemGroup,
} from "@/api/systemGroups";
import { errorFactory } from "./testutils";

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

describe("Test Group Definition", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    jest.useFakeTimers();
    // @ts-expect-error ts complains about history on VueRouter
    if (router.history.current.path != "/system_group/new") {
      router.push({ name: "New Group" });
    }
  });
  it("Test new group", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
    });
    await flushPromises();
    expect(wrapper.findAll("input").length).toBe(3);

    wrapper.find("input[type=checkbox]").setChecked();
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    expect(updateSystemGroup).not.toHaveBeenCalled();
    expect(createSystemGroup).toHaveBeenCalled();
  });
  it("Test new group failure", async () => {
    // @ts-expect-error throws an error
    createSystemGroup.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
    });
    await flushPromises();
    expect(wrapper.findAll("input").length).toBe(3);

    wrapper.find("input[type=checkbox]").setChecked();
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    expect(wrapper.find(".error-list").exists()).toBeTruthy();
  });
  it("Test update group", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
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
    expect(wrapper.findAll("input").length).toBe(3);

    wrapper.find("input[type=checkbox]").setChecked();
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    jest.runAllTimers();
    expect(createSystemGroup).not.toHaveBeenCalled();
    expect(updateSystemGroup).toHaveBeenCalled();
  });
  it("Test update group failure", async () => {
    // @ts-expect-error throws an error
    updateSystemGroup.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
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
    expect(wrapper.findAll("input").length).toBe(3);

    wrapper.find("input[type=checkbox]").setChecked();
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    jest.runAllTimers();
    expect(wrapper.find(".errors-list").exists());
  });
  it("Test update group remove systems", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
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
    expect(wrapper.findAll("input").length).toBe(3);

    wrapper.find("input[type=checkbox]").setChecked(false);
    await flushPromises();
    wrapper.find("button[type='submit']").trigger("click");
    await flushPromises();
    jest.runAllTimers();
    expect(createSystemGroup).not.toHaveBeenCalled();
    expect(updateSystemGroup).toHaveBeenCalled();
    expect(removeSystemFromSystemGroup).toHaveBeenCalled();
  });
  it("Test load systems failure", async () => {
    // @ts-expect-error throws an error
    listSystems.mockImplementationOnce(async () => {
      throw errorFactory("error");
    });
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
    });
    await flushPromises();
    expect(wrapper.findAll("input").length).toBe(1);
    expect(wrapper.find(".error-list").exists()).toBeTruthy();
  });
  it("Test update group group dne", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(GroupDefinition, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        groupId: "04558a7e-c028-11ec-9d64-0242ac120002",
      },
    });
    await flushPromises();
    expect(wrapper.findAll("input").length).toBe(0);
  });
});
