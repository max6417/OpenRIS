document.addEventListener('DOMContentLoaded', () => {
    let dropdown = document.querySelector('.dropdown-trigger');
    M.Dropdown.init(dropdown, {
        coverTrigger: false,
        constainWidth: false
    });
});