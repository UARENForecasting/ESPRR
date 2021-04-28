export function errorFactory(error: string): Record<string, any> {
  return {
    detail: [
      {
        loc: ["theError"],
        msg: error,
      },
    ],
  };
}
