module.exports = {
  preset: "@vue/cli-plugin-unit-jest/presets/typescript-and-babel",
  collectCoverage: true,
  collectCoverageFrom: ["<rootDir>/src/**/*.ts", "<rootDir>/src/**/*.vue"],
  moduleFileExtensions: ["ts", "vue", "js"],
  moduleNameMapper: {
    "\\.(css|less)$": "<rootDir>/tests/cssstub.js",
  },
  setupFilesAfterEnv: ["<rootDir>/jest-setup.ts"],
};
