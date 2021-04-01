(function() {
'use strict';

const fields = document.querySelectorAll('input, textarea');
for (let i = 0; i < fields.length; ++i) {
  fields[i].addEventListener('blur', (e) => {
    e.target.classList.add('interacted');
  });
}


if (document.querySelector('#cancel-button')) {
  document.querySelector('#cancel-button').addEventListener('click', (e) => {
    window.location.href = `/guide/edit/${e.currentTarget.dataset.id}`;
  });
}


document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.remove('loading');
});
})();
