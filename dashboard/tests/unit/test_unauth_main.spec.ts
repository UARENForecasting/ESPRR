import { Auth0Plugin } from "@/auth/auth";

import flushPromises from "flush-promises";

jest.mock("@/auth/auth");
jest.mock("@/api/systems");

describe("Test main", () => {
  it("unauth home", async () => {
    Auth0Plugin.install = jest.fn().mockImplementationOnce((Vue: any) => {
      Vue.prototype.$auth = {
        isAuthenticated: false,
        loading: false,
      };
    });
    document.body.innerHTML = '<div id="app"></div>';

    require("../../src/main");

    await flushPromises();
    // @ts-expect-error possibly null
    expect(document.querySelector("main").textContent.trim()).toContain(
      "Please log in to access ESPRR."
    );
  });
});
