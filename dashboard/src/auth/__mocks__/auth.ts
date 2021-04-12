/* istanbul ignore file */
/*
 * Module for mocking Auth0 plugin during testing.
 */
import { VueConstructor } from "vue";

const user = {
  email: "testing@esprr.x.energy.arizona.edu",
  email_verified: true,
  sub: "auth0|6061d0dfc96e2800685cb001",
};

export const $auth = {
  isAuthenticated: true,
  loading: false,
  user: user,
  logout: jest.fn(),
  loginWithRedirect: jest.fn(),
  getTokenSilently: jest.fn().mockResolvedValue("Token"),
};

export const Auth0Plugin = {
  /* eslint-disable-next-line @typescript-eslint/no-unused-vars */
  install(Vue: VueConstructor, options: Record<string, any>): void {
    Vue.prototype.$auth = $auth;
  },
};
