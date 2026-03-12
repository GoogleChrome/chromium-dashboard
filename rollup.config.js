import rollupResolve from '@rollup/plugin-node-resolve';
import terser from '@rollup/plugin-terser';

export default {
  input: [
    'build/components.js',
    'build/js-src/openapi-client.js',
    'build/js-src/cs-client.js',
    'build/js-src/shared.js',
  ],
  output: {
    dir: 'static/dist',
    format: 'es',
    sourcemap: true,
    compact: true,
  },
  plugins: [
    rollupResolve(),
    terser({
      format: {
        comments: false,
      },
      ecma: 2020,
      module: true,
      warnings: true,
      mangle: false,
    }),
  ],
  onwarn: function(warning, warn) {
    if (warning.code === 'THIS_IS_UNDEFINED') return;
    warn(warning);
  },
};
