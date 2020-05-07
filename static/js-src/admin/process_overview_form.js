(function() {
'use strict';

// Only admins see this button
if (document.querySelector('.delete-button')) {
  document.querySelector('.delete-button').addEventListener('click', (e) => {
    if (!confirm('Delete feature?')) {
      return;
    }

    fetch(`/admin/features/delete/${e.currentTarget.dataset.id}`, {
      method: 'POST',
      credentials: 'include',
    }).then((resp) => {
      if (resp.status === 200) {
        location.href = '/features';
      }
    });
  });
}


document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.remove('loading');
});
})();
