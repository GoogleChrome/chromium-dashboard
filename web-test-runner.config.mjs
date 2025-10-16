export default {
  files: 'build/**/*_test.{js,ts}',
  concurrentBrowsers: 1,
  concurrency: 1,
  nodeResolve: true,
  browserStartTimeout: 60000,
  filterBrowserLogs(log) {
      // Suppress the "Lit is in dev mode" warning
      if (log.args.some((arg) => typeof arg === 'string' && arg.includes('Lit is in dev mode'))) {
        return false;
      }

      // Allow all other logs to pass through
      return true;
    },
};
