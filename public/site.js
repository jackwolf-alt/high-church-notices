'use strict';
// A deliberately local demonstration: no accounts, requests or stored searches.
const search = document.querySelector('#example-search');
if (search) {
  const notices = [...document.querySelectorAll('.example-notice')];
  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase('en-GB');
    let count = 0;
    for (const notice of notices) {
      const match = notice.dataset.search.includes(query);
      notice.hidden = !match;
      if (!match) notice.open = false;
      if (match) count++;
    }
    document.querySelector('#example-count').textContent = `${count} example notice${count === 1 ? '' : 's'}`;
    document.querySelector('#example-empty').hidden = count > 0;
  });
}
