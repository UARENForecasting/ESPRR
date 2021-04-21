import { getDisplayName } from "@/utils/DisplayNames";

describe("Test get display names", () => {
  it("test exists", () => {
    expect(getDisplayName("ac_capacity")).toBe("AC Capacity");
    expect(getDisplayName("gcr")).toBe("Ground Coverage Ratio");
  });
  it("Test does not exist", () => {
    expect(getDisplayName("banana")).toBe("banana");
  });
});
