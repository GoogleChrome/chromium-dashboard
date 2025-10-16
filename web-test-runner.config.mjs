const filteredLogs = [
  'Lit is in dev mode',
];

export default {
  files: 'build/**/*_test.{js,ts}',
  concurrentBrowsers: 1,
  concurrency: 1,
  nodeResolve: true,
  browserStartTimeout: 60000,
  filterBrowserLogs(log) {
    for (const arg of log.args) {
      if (typeof arg === 'string' && filteredLogs.some(l => arg.includes(l))) {
        return false;
      }
    }

    return true;
  },
};
