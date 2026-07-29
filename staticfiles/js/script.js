// Check for saved user preference, if any, on load
const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;

if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);
}

// Function to handle the toggle switch in the Settings page
document.addEventListener('DOMContentLoaded', (event) => {
    const toggleSwitch = document.querySelector('#theme-toggle');
    
    if (toggleSwitch) {
        // Set toggle state based on current theme
        if (currentTheme === 'dark') {
            toggleSwitch.checked = true;
        }

        // Listen for changes
        toggleSwitch.addEventListener('change', function(e) {
            if (e.target.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }    
        });
    }
});


document.addEventListener('DOMContentLoaded', () => {
    // Balance Toggle Logic
    const balanceEl = document.getElementById('account-balance');
    const toggleIcon = document.getElementById('toggle-balance');

    if (balanceEl && toggleIcon) {
        // Save the real balance string
        const actualBalance = balanceEl.getAttribute('data-balance');
        const hiddenBalance = '****';
        let isHidden = false;

        toggleIcon.addEventListener('click', () => {
            isHidden = !isHidden;
            if (isHidden) {
                balanceEl.textContent = hiddenBalance;
                // Swap the FontAwesome icon to closed eye
                toggleIcon.classList.remove('fa-eye-slash');
                toggleIcon.classList.add('fa-eye');
            } else {
                balanceEl.textContent = actualBalance;
                // Swap back to open eye
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            }
        });
    }
});
