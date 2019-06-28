document.querySelector('chromedash-metrics').addEventListener('app-ready', function() {
  console.log('app ready');
  document.body.classList.remove('loading');
});
