/** Climate, market, buyer & yield modules stay disabled until the pilot validates diagnosis. */
export const flags = {
  climate: process.env.NEXT_PUBLIC_FLAG_CLIMATE === "true",
  market: process.env.NEXT_PUBLIC_FLAG_MARKET === "true",
};
