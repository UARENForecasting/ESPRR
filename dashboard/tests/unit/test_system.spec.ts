import System from "@/views/System.vue";
import { $auth } from "./mockauth";
import {
  getSystem,
  listSystems,
  deleteSystem,
  getResult,
  getResultTimeseries,
  getResultStatistics,
  fetchResultTimeseries,
  fetchResultStatistics,
} from "@/api/systems";

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

describe("Test System Details/Results page", () => {
  beforeEach(() => {
    jest.resetModules();
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("Test System With results", async () => {
    const wrapper = mount(System, {
      localVue,
      router,
      mocks,
      stubs,
    });

    await flushPromises();
  });
});
