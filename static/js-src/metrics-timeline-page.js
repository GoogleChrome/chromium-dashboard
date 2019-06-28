const timelineEl = document.querySelector('chromedash-timeline');
timelineEl.props = DATA;
console.log(timelineEl.props);

document.body.classList.remove('loading');

window.addEventListener('popstate', function(e) {
  if (e.state) {
    timelineEl.selectedBucketId = e.state.id;
  }
});
