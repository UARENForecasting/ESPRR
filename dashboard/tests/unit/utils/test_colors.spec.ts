import getColor from "@/utils/Colors";

describe("Test get a color", () => {
  it("test exists", () => {
    expect(getColor(0)).toBe("#e6194B");
  });
});
