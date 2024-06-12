import {playwrightLauncher} from '@web/test-runner-playwright';

export default {
  browsers: [
    playwrightLauncher({product: 'chromium'}),
    playwrightLauncher({product: 'firefox'}),
  ],
  files: 'static/js/**/*.test.js', // Adjust this line to point to the static/js directory
};
