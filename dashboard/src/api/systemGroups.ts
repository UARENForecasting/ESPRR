/* istanbul ignore file */

import { Table } from "apache-arrow";
import { PVSystemGroup, StoredPVSystemGroup } from "@/models";

export async function listSystemGroups(
  token: string
): Promise<Array<StoredPVSystemGroup>> {
  const response = await fetch("/api/system_groups/", {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
  });
  if (response.ok) {
    const systemsList = response.json();
    return systemsList;
  } else {
    console.error(
      `Failed to load system groups with status code ${response.status}`
    );
    return [];
  }
}

export async function getSystemGroup(
  token: string,
  groupId: string
): Promise<StoredPVSystemGroup> {
  const response = await fetch(`/api/system_groups/${groupId}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
  });
  if (response.ok) {
    const group = response.json();
    return group;
  } else {
    throw `Failed to load system group with status code ${response.status}`;
  }
}

export async function deleteSystemGroup(
  token: string,
  groupId: string
): Promise<void> {
  const response = await fetch(`/api/system_groups/${groupId}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
    method: "delete",
  });
  if (!response.ok) {
    throw `Could not delete system group ${groupId}`;
  }
}

export async function createSystemGroup(
  token: string,
  definition: PVSystemGroup
): Promise<StoredPVSystemGroup> {
  const response = await fetch("/api/system_groups/", {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    method: "post",
    body: JSON.stringify(definition),
  });
  if (response.ok) {
    return await response.json();
  } else if (response.status == 422) {
    throw await response.json();
  } else if (response.status == 409) {
    throw {
      detail: [
        {
          loc: ["body", "name"],
          msg: `System Group with name ${definition.name} already exists`,
        },
      ],
    };
  } else {
    throw {
      detail: [
        {
          loc: ["system"],
          msg: "Could not create system group",
        },
      ],
    };
  }
}

export async function updateSystemGroup(
  token: string,
  groupId: string,
  definition: PVSystemGroup
): Promise<StoredPVSystemGroup> {
  const response = await fetch(`/api/system_groups/${groupId}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    method: "post",
    body: JSON.stringify(definition),
  });
  if (response.ok) {
    return await response.json();
  } else if (response.status == 422) {
    throw await response.json();
  } else if (response.status == 409) {
    throw {
      detail: [
        {
          loc: ["body", "name"],
          msg: `System Group with name ${definition.name} already exists`,
        },
      ],
    };
  } else {
    throw "Could not create system group";
  }
}

export async function addSystemToSystemGroup(
  token: string,
  groupId: string,
  systemId: string
): Promise<void> {
  const response = await fetch(
    `/api/system_groups/${groupId}/systems/${systemId}`,
    {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      }),
      method: "post",
    }
  );
  if (response.ok) {
    return await response.json();
  } else if (response.status == 422) {
    throw await response.json();
  } else {
    throw "Could not add system ${systemId} to group";
  }
}

export async function removeSystemFromSystemGroup(
  token: string,
  groupId: string,
  systemId: string
): Promise<void> {
  const response = await fetch(
    `/api/system_groups/${groupId}/systems/${systemId}`,
    {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      }),
      method: "delete",
    }
  );
  if (response.ok) {
    return await response.json();
  } else if (response.status == 422) {
    throw await response.json();
  } else {
    throw "Could not add system ${systemId} to group";
  }
}

// TODO: BELOW
export async function startProcessing(
  token: string,
  systemId: string,
  dataset: string
): Promise<Record<string, any>> {
  const response = await fetch(`/api/systems/${systemId}/data/${dataset}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    method: "post",
  });
  if (response.ok) {
    return await response.json();
  } else {
    throw await response.json();
  }
}
export async function getResult(
  token: string,
  systemId: string,
  dataset: string
): Promise<Record<string, any>> {
  const response = await fetch(`/api/systems/${systemId}/data/${dataset}`, {
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
    method: "get",
  });
  if (response.ok) {
    return await response.json();
  } else {
    const errors = response.json();
    throw errors;
  }
}

export async function fetchResultTimeseries(
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  const response = await fetch(
    `/api/systems/${systemId}/data/${dataset}/timeseries`,
    {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
        Accept: accept,
      }),
      method: "get",
    }
  );
  return response;
}
export async function getResultTimeseries(
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Table | string> {
  const response = await fetchResultTimeseries(
    token,
    systemId,
    dataset,
    accept
  );
  if (response.ok) {
    if (accept == "application/vnd.apache.arrow.file") {
      const data = await response.arrayBuffer();
      return Table.from([new Uint8Array(data)]);
    } else {
      return await response.text();
    }
  } else {
    const errors = await response.json();
    throw errors;
  }
}

export async function fetchResultStatistics(
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Response> {
  const response = await fetch(
    `/api/systems/${systemId}/data/${dataset}/statistics`,
    {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
        Accept: accept,
      }),
      method: "get",
    }
  );
  return response;
}
export async function getResultStatistics(
  token: string,
  systemId: string,
  dataset: string,
  accept = "application/vnd.apache.arrow.file"
): Promise<Table | string> {
  const response = await fetchResultStatistics(
    token,
    systemId,
    dataset,
    accept
  );
  if (response.ok) {
    if (accept == "application/vnd.apache.arrow.file") {
      const data = await response.arrayBuffer();
      return Table.from([new Uint8Array(data)]);
    } else {
      return await response.text();
    }
  } else {
    const errors = await response.json();
    throw errors;
  }
}
