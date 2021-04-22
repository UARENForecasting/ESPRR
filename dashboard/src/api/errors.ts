import { getDisplayName } from "@/utils/DisplayNames";

export default function flattenErrors(
  errors: Record<string, any>
): Record<string, any> {
  const flattened: Record<string, any> = {};
  for (const e of errors.detail) {
    let field: string;
    field = e.loc[e.loc.length - 1];
    if (field == "__root__") {
      field = "System";
    } else {
      field = getDisplayName(field);
    }
    const errorString = e.msg;
    flattened[field] = errorString;
  }
  return flattened;
}
