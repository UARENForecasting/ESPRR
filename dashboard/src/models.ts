export interface FixedTracking {
  tilt: number;
  azimuth: number;
}

export interface SingleAxisTracking {
  axis_tilt: number;
  axis_azimuth: number;
  gcr: number;
  backtracking: boolean;
}

export interface LatLon {
  latitude: number;
  longitude: number;
}

export interface BoundingBox {
  nw_corner: LatLon;
  se_corner: LatLon;
}

export interface PVSystem {
  name: string;
  boundary: BoundingBox;
  tracking: FixedTracking | SingleAxisTracking;
  ac_capacity: number;
  dc_ac_ratio: number;
  albedo: number;
}

export interface StoredPVSystem {
  created_at: string;
  modified_at: string;
  object_id: string;
  object_type: string;
  definition: PVSystem;
}

export interface PVSystemGroup {
  name: string;
  systems?: Array<StoredPVSystem>;
}

export interface StoredPVSystemGroup {
  created_at: string;
  modified_at: string;
  object_id: string;
  object_type: string;
  definition: PVSystemGroup;
}
