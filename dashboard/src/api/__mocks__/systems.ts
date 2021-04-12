/* Provides default mock values for systems api module.
 * Each exported function is mocked with a jest.fn.
 *
 * Use by calling jest.mock("@/api/systems") in test.
 *
 * Results may be mocked by importing the original function
 * e.g. import { listSystems } from "@/api/systems"
 * and calling listSystems.mockResolvedValues.
 */
const systems = [
  {
    object_id: "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
    object_type: "system",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Test PV System",
      boundary: {
        nw_corner: {
          latitude: 34.9,
          longitude: -112.9,
        },
        se_corner: {
          latitude: 33,
          longitude: -111,
        },
      },
      ac_capacity: 10,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: {
        tilt: 20,
        azimuth: 180,
      },
    },
  },
  {
    object_id: "6b61d9ac-2e89-11eb-be2a-4dc7a6bhe0a9",
    object_type: "system",
    created_at: "2020-12-01T01:23:00+00:00",
    modified_at: "2020-12-01T01:23:00+00:00",
    definition: {
      name: "Real PV System",
      boundary: {
        nw_corner: {
          latitude: 34.9,
          longitude: -112.9,
        },
        se_corner: {
          latitude: 33,
          longitude: -111,
        },
      },
      ac_capacity: 10,
      dc_ac_ratio: 1.2,
      albedo: 0.2,
      tracking: {
        tilt: 20,
        azimuth: 180,
      },
    },
  },
];

const listSystems = jest.fn().mockResolvedValue(systems);

export { listSystems };
