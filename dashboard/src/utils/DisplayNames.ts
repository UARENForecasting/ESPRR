export const displayNames: Record<string, any> = {
  ac_capacity: "AC Capacity",
  dc_ac_ratio: "DC/AC Ratio",
  albedo: "Albedo",
  tilt: "Tilt",
  azimuth: "Azmuth",
  axis_tilt: "Axis Tilt",
  axis_azimuth: "Axis Azimuth",
  gcr: "Ground Coverage Ratio",
  backtracking: "Backtracking",
  ac_power: "AC Power",
  clearsky_ac_power: "Clearsky AC Power",
  "p95 daytime ramp": "Stress-case up (p95)",
  "p05 daytime ramp": "Stress-case down (p05)",
  "typical sunrise ramp": "Typical Sunrise",
  "typical sunset ramp": "Typical Sunset",
  NSRDB_2019: "NSRDB 2019",
};

export function getDisplayName(machineName: string): string {
  if (!(machineName in displayNames)) {
    return machineName;
  } else {
    return displayNames[machineName];
  }
}
