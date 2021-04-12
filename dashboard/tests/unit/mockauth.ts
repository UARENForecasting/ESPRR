// module for mocking auth on individual components
import * as auth from "@/auth/auth";

const mockedAuthInstance = jest.spyOn(auth, "getInstance");

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

beforeEach(() => {
  $auth.isAuthenticated = true;
  $auth.loading = false;
  $auth.user = user;
  $auth.logout = jest.fn();
  $auth.loginWithRedirect = jest.fn();
  $auth.getTokenSilently = jest.fn().mockResolvedValue("Token");
});

// @ts-expect-error ignore type complaints for mock
mockedAuthInstance.mockImplementation(() => $auth);

export { mockedAuthInstance, $auth };
