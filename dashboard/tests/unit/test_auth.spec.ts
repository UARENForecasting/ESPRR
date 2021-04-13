/* Tests for auth module and integration are a modified version of those used
 * by Solar Performance Insight which carries the following license:
 *
 * MIT License
 *
 * Copyright (c) 2020 SolarPerformanceInsight
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
import Vue from "vue";
import VueRouter from "vue-router";
import { createLocalVue, mount } from "@vue/test-utils";
import flushPromises from "flush-promises";

import App from "@/App.vue";
import router from "@/router";

import { $auth } from "./mockauth";
import { User } from "@/auth/User";

jest.mock("@/api/systems");

const localVue = createLocalVue();

const mocks = {
  $auth,
};

localVue.use(VueRouter);

describe("Tests authenticated routes", () => {
  beforeEach(() => {
    $auth.isAuthenticated = false;
    jest.clearAllMocks();
    // @ts-expect-error ts complains about history on VueRouter
    if (router.history.current.path != "/") {
      router.push({ name: "Systems" });
    }
  });
  it("unauthenticated home", async () => {
    const home = mount(App, {
      localVue,
      router,
      mocks,
    });
    await flushPromises();
    expect(home.find("main").text()).toBe("Please log in to access ESPRR.");
    const button = home.find("button");
    expect(button.text()).toMatch(/Log in/);
    expect($auth.loginWithRedirect).not.toHaveBeenCalled();
    await button.trigger("click");
    expect($auth.loginWithRedirect).toHaveBeenCalled();
    expect($auth.logout).not.toHaveBeenCalled();
  });
});

describe("Tests authenticated routes", () => {
  beforeEach(() => {
    $auth.isAuthenticated = true;
    jest.clearAllMocks();
    // @ts-expect-error ts complains about history on VueRouter
    if (router.history.current.path != "/") {
      router.push({ name: "Systems" });
    }
  });
  it("authenticated home", async () => {
    const home = mount(App, {
      localVue,
      router,
      mocks,
    });
    await flushPromises();
    expect(home.find("Table").text()).toBe(
      "Name AC Capacity (MW) Tracking Test PV System 10  Fixed Real PV System 10  Fixed"
    );
    const button = home.find("button");
    expect(button.text()).toMatch(/Log out/);
    expect($auth.logout).not.toHaveBeenCalled();
    await button.trigger("click");
    expect($auth.logout).toHaveBeenCalled();
    expect($auth.loginWithRedirect).not.toHaveBeenCalled();
  });
});

describe("Test authguard", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // @ts-expect-error ts complains about history on VueRouter
    if (router.history.current.path != "/") {
      router.push({ name: "Systems" });
    }
  });

  it("test unauthenticated access to protected route", async () => {
    $auth.isAuthenticated = false;
    const view = mount(App, {
      localVue,
      router,
      mocks,
    });
    expect(view.find("main").text()).toMatch(/Please log in to access ESPRR./);
    expect($auth.loginWithRedirect).not.toHaveBeenCalled();
    router.push({ name: "New System" });
    await Vue.nextTick();
    expect($auth.loginWithRedirect).toHaveBeenCalled();
    // assert view has not changed since loginWithRedirect is mocked and does
    // nothing
    expect(view.find("main").text()).toMatch(/Please log in to access ESPRR./);
  });
  it("test authenticated access to protected route", async () => {
    $auth.isAuthenticated = true;
    const view = mount(App, {
      localVue,
      router,
      mocks,
    });
    await flushPromises();
    expect(view.find("main").text()).toMatch(
      "Name AC Capacity (MW) Tracking Test PV System 10  Fixed Real PV System 10  Fixed"
    );
    expect($auth.loginWithRedirect).not.toHaveBeenCalled();
    router.push({ name: "New System" });
    await Vue.nextTick();
    expect($auth.loginWithRedirect).not.toHaveBeenCalled();
    // Assert view at new path is rendered
    expect(view.find("main").text()).toBe("TODO");
  });
});

describe("test user", () => {
  it("instantiate a user object", () => {
    const user = {
      sub: "auth0|somestuff",
      names: "names",
      nickname: "rick",
      picture: "http://www.photobucket.com/rickvacation",
      updated_at: "2222-22-22T22:22:22-10:00",
    };
    const expected = {
      sub: "auth0|somestuff",
      provider: "auth0",
      id: "somestuff",
      names: "names",
      nickname: "rick",
      picture: "http://www.photobucket.com/rickvacation",
      updated_at: "2222-22-22T22:22:22-10:00",
    };
    const instance = new User(user);
    expect(instance).toEqual(expected);
  });
  it("instantiate a user object from falsey", () => {
    // @ts-expect-error null not in constructor types, test it anyway
    expect(new User(null)).toEqual({});
  });
});
