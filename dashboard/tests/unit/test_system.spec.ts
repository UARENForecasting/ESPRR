import System from "@/views/System.vue";
import { $auth } from "./mockauth";
import { deleteSystem } from "@/api/systems";

import { createLocalVue, mount } from "@vue/test-utils";
import VueRouter from "vue-router";
import router from "@/router";
import flushPromises from "flush-promises";

// use systems mock module
jest.mock("@/api/systems");

const localVue = createLocalVue();
localVue.use(VueRouter);

const mocks = { $auth };
const stubs = {
  "system-map": true,
};

describe("Test System Details/Results page", () => {
  beforeEach(() => {
    jest.resetModules();
    if (
      // @ts-expect-error ts complains about history on VueRouter
      router.history.current.path !=
      "/system/6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9"
    ) {
      router.push({
        name: "System Details",
        params: {
          systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
        },
      });
    }
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test System With results", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(System, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
      },
    });

    await flushPromises();

    // @ts-expect-error accessing Vue subclass getter
    expect(wrapper.vm.otherSystems[0].object_id);
    appTarget.remove();
  });
  it("Test delete system error", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(System, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
        dataset: "NSRDB_2019",
      },
    });

    // @ts-expect-error ts does not recognize mocked fn
    deleteSystem.mockImplementationOnce(async () => {
      throw "error";
    });

    await flushPromises();
    expect(wrapper.find(".modal-block").exists()).toBe(false);
    wrapper.find("button.delete-system").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe(
      "/system/6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9"
    );
    appTarget.remove();
  });
  it("Test delete system", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(System, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
      },
    });

    await flushPromises();
    expect(wrapper.find(".modal-block").exists()).toBe(false);
    wrapper.find("button.delete-system").trigger("click");

    await flushPromises();

    wrapper.find(".confirm-deletion").trigger("click");

    await flushPromises();
    // @ts-expect-error ts compains about history on VueRouter
    expect(router.history.current.path).toBe("/");
    appTarget.remove();
  });
  it("Test system dne", async () => {
    const appTarget = document.createElement("div");
    appTarget.id = "app";
    document.body.appendChild(appTarget);

    const wrapper = mount(System, {
      attachTo: "#app",
      localVue,
      router,
      mocks,
      stubs,
      propsData: {
        systemId: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
        dataset: "NSRDB_2019",
      },
    });

    await flushPromises();
    expect(wrapper.text()).toBe("The System could not be found");
    appTarget.remove();
  });
});
