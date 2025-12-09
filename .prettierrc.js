import gts from 'gts/.prettierrc.json' with { type: "json" };

/** @type {import("prettier").Config} */
export default {
  ...gts,
  "trailingComma": "es5",
};
