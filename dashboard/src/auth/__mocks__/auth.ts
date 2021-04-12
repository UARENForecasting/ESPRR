/* istanbul ignore file */
/* Provides default mock values for auth module. This is only useful
 * when we want to mount the entire app via main.ts.
 *
 * Default will be an authenticated user.
 *
 * Use by calling jest.mock("@/auth/auth") in test.
 *
 * Values may be altered by mocking the implementation of the install
 * function to supply a different $auth object.
 *
 * Note that when import main, a vue app is initialized on the DOM,
 * so tests should be placed in separate spec files. This is to
 * initialize a fresh DOM/app between tests.
 *
 * For testing individual components, use `tests/units/mockauth.ts`.
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
