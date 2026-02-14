document.addEventListener('DOMContentLoaded', () => {
    const verseNums = document.querySelectorAll('.verse-num');
    
    verseNums.forEach(num => {
        num.style.cursor = 'pointer';
        num.title = 'Click to copy verse link';
        
        num.addEventListener('click', (e) => {
            const verseRow = e.target.closest('.verse-row');
            const verseId = verseRow.id;
            const url = window.location.href.split('#')[0] + '#' + verseId;
            
            navigator.clipboard.writeText(url).then(() => {
                // Show a temporary tooltip or toast
                const originalTitle = num.title;
                num.setAttribute('data-bs-original-title', 'Copied!');
                
                // Use Bootstrap tooltip if available, otherwise simple alert/console
                // For simplicity, let's just log or change color briefly
                const originalColor = num.style.color;
                num.style.color = '#28a745'; // Green
                
                setTimeout(() => {
                    num.style.color = originalColor;
                }, 1000);
            });
        });
    });
});
