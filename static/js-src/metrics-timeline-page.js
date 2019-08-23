const timelineEl = document.querySelector('chromedash-timeline');
timelineEl.props = DATA;

document.body.classList.remove('loading');

window.addEventListener('popstate', function(e) {
  if (e.state) {
    timelineEl.selectedBucketId = e.state.id;
  }
});
