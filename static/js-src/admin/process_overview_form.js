(function() {
'use strict';

// Only admins see this button
if (document.querySelector('.delete-button')) {
  document.querySelector('.delete-button').addEventListener('click', (e) => {
    if (!confirm('Delete feature?')) {
      return;
    }

    fetch(`/api/v0/features/${e.currentTarget.dataset.id}`, {
      method: 'DELETE',
      credentials: 'include',
    }).then((resp) => {
      if (resp.status === 200) {
        location.href = '/features';
      }
    });
  });
}


if (document.querySelector('#open-metadata')) {
  document.querySelector('#open-metadata').addEventListener('click', (e) => {
    document.querySelector('#metadata-readonly').style.display = 'none';
    document.querySelector('#metadata-editing').style.display = '';
  });
}

if (document.querySelector('#close-metadata')) {
  document.querySelector('#close-metadata').addEventListener('click', (e) => {
    document.querySelector('#metadata-readonly').style.display = '';
    document.querySelector('#metadata-editing').style.display = 'none';
  });
}


document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.remove('loading');
});
})();
