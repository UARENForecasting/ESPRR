/* istanbul ignore file */

import { StoredPVSystem, PVSystem } from "@/models";

export async function listSystems(
  token: string
): Promise<Array<StoredPVSystem>> {
  const response = await fetch("/api/systems/", {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
  });
  if (response.ok) {
    const systemsList = response.json();
    return systemsList;
  } else {
    console.error(`Failed to load systems with status code ${response.status}`);
    return [];
  }
}

export async function getSystem(
  token: string,
  systemId: string
): Promise<StoredPVSystem> {
  const response = await fetch(`/api/systems/${systemId}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
  });
  if (response.ok) {
    const system = response.json();
    return system;
  } else {
    throw `Failed to load systems with status code ${response.status}`;
  }
}

export async function deleteSystem(
  token: string,
  systemId: string
): Promise<void> {
  const response = await fetch(`/api/systems/${systemId}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
    method: "delete",
  });
  if (!response.ok) {
    throw `Could not delete system ${systemId}`;
  }
}

export async function createSystem(
  token: string,
  definition: PVSystem
): Promise<Record<string, any> | null> {
  const response = await fetch("/api/systems/", {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
    method: "post",
    body: JSON.stringify(definition),
  });
  if (response.ok) {
    return await response.json();
  } else if (response.status == 422) {
    throw await response.json();
  } else if (response.status == 409) {
    throw `Site with name ${definition.name} already exists`;
  } else {
    throw "Could not create system";
  }
}
