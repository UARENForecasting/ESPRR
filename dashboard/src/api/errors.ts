export default function flattenErrors(
  errors: Record<string, any>
): Record<string, any> {
  const flattened: Record<string, any> = {};
  for (const e of errors.detail) {
    const field = e.loc[e.loc.length - 1];
    const errorString = e.msg;
    flattened[field] = errorString;
  }
  return flattened;
}
