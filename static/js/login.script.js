document.addEventListener('DOMContentLoaded', function() {
    var themeToggle = document.getElementById('theme-toggle');
    var isDarkMode = localStorage.getItem('darkMode') === 'true';

    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i> Toggle Light Mode';
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i> Toggle Dark Mode';
    }
    
    function enableDarkMode() {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i> Toggle Light Mode';
        localStorage.setItem('darkMode', 'true');
    }
    
    function disableDarkMode() {
        document.body.classList.remove('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i> Toggle Dark Mode';
        localStorage.setItem('darkMode', 'false');
    }
    
    themeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });
});
