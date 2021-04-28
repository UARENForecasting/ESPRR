import Results from "@/components/Results.vue";
import { $auth } from "./mockauth";
import { systems } from "@/api/__mocks__/systems";
import { getResult } from "@/api/systems";

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
  });
});
