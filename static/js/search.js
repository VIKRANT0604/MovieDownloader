// Enable live search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form[action="/search"]');
    const searchInput = searchForm.querySelector('input[name="q"]');
    
    let timeout = null;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(timeout);
        
        timeout = setTimeout(() => {
            if (this.value.length >= 2) {
                searchForm.submit();
            }
        }, 500);
    });
});
