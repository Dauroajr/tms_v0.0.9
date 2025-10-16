

document.addEventListener('DOMContentLoaded', () => {
  const dropdownElements = document.querySelectorAll('.dropdown');

  dropdownElements.forEach(dropdown => {
    let showTimeout, hideTimeout;

    dropdown.addEventListener('mouseover', () => {
      clearTimeout(hideTimeout);
      showTimeout = setTimeout(() => {
        dropdown.querySelector('.dropdown-menu').classList.add('show');
      }, 200);  // 0.4 seconds delay
    });

    dropdown.addEventListener('mouseout', () => {
      clearTimeout(showTimeout);
      hideTimeout = setTimeout(() => {
        dropdown.querySelector('.dropdown-menu').classList.remove('show');
      }, 200);  // You can also set a delay for hiding, if needed
    });
  });
});
