/* istanbul ignore file */
/*
 * Module for mocking Auth0 plugin during testing.
 */
const user = {
  email: "testing@esprr.x.energy.arizona.edu",
  email_verified: true,
  sub: "auth0|6061d0dfc96e2800685cb001",
};

const $auth = {
  isAuthenticated: true,
  loading: false,
  user: user,
  logout: jest.fn(),
  loginWithRedirect: jest.fn(),
  getTokenSilently: jest.fn().mockResolvedValue("Token"),
};

const install = jest.fn().mockImplementation((Vue: any) => {
  Vue.prototype.$auth = $auth;
});

const Auth0Plugin = {
  install: install,
};

// Add getInstance as a jest fn, so the component specific
// mocking module at /tests/unit/mockauth.ts can be used to import
// $auth without hitting an undefined getInstance function.
const getInstance = jest.fn().mockResolvedValue($auth);
export { Auth0Plugin, getInstance };
