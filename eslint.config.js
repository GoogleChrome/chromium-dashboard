import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import gts from "./node_modules/gts/build/src/index.js";


export default [
  js.configs.recommended,
  eslintConfigPrettier,
  {
    rules: gts.rules,
  },
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        "ga": true,
        "Metric": true
      },
    },
    rules: {
      "no-warning-comments": "off",
      "no-unused-vars": ["error", {
        "vars": "all",
        "args": "after-used",
        "argsIgnorePattern": "^var_args$"
      }],
      "require-jsdoc": 0,
      "valid-jsdoc": "off",
      "no-var": 1,
      "prettier/prettier": "off",
      // TODO: Re-enable these rules from gts.
      "eqeqeq": "off",
      "no-const-assign": "off",
      "no-dupe-class-members": "off",
      "no-dupe-keys": "off",
      "no-empty-pattern": "off",
      "no-prototype-builtins": "off",
      "no-self-assign": "off",
      "no-undef": "off",
      "no-unreachable": "off",
      "no-useless-escape": "off",
      "node/no-extraneous-import": "off",
      "node/no-missing-import": "off",
      "node/no-unpublished-import": "off",
    },
    ignores: [
      "**/node_modules/**",
      "static/dist/",
    ]
  }
];
