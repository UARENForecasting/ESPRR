import flushPromises from "flush-promises";

jest.mock("@/auth/auth");
jest.mock("@/api/systems");

describe("Test main", () => {
  it("home", async () => {
    document.body.innerHTML = '<div id="app"></div>';

    await flushPromises();
    require("../../src/main");

    // @ts-expect-error possible null
    expect(document.querySelector("h1").textContent).toEqual("ESPRR");
    // @ts-expect-error possible null
    expect(document.querySelector("h2").textContent).toEqual("Systems");
  });
});
