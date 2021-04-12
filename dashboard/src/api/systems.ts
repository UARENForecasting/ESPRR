export async function listSystems(
  token: string
): Promise<Array<Record<string, any>>> {
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
