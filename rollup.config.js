import resolve from 'rollup-plugin-node-resolve';
import { terser } from 'rollup-plugin-terser';

const production = !process.env.ROLLUP_WATCH;

export default {
  input: 'static/js/component-bundle-entry.js',
  output: {
    file: 'static/js/component-bundle.js',
    format: 'iife', // immediately-invoked function expression — suitable for <script> tags
    sourcemap: true
  },
  plugins: [
    resolve(), // tells Rollup how to find node_modules
    production && terser() // minify, but only in production
  ]
};
