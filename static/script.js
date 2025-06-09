document.addEventListener('DOMContentLoaded', function () {
    const input = document.querySelector('.url-input');
    const summaryBox = document.querySelector('.summary-box');
    const thumbnailContainer = document.getElementById('thumbnail-container');
    const summarizeButton = document.getElementById('summarize-button');

    const fetchSummary = () => {
        if (!input.value.trim()) {
            summaryBox.textContent = 'Please enter a YouTube URL';
            thumbnailContainer.innerHTML = '';
            return;
        }

        console.log('Fetching summary for URL:', input.value);
        summaryBox.textContent = 'Loading summary...';
        thumbnailContainer.innerHTML = '';
        summaryBox.innerHTML = '';

        fetch('/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: input.value })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    summaryBox.textContent = `Error: ${data.error}`;
                    thumbnailContainer.innerHTML = '';
                } else {
                    if (data.thumbnail_url) {
                        const img = document.createElement('img');
                        img.src = data.thumbnail_url;
                        img.alt = 'Video Thumbnail';
                        img.classList.add('video-thumbnail');
                        thumbnailContainer.appendChild(img);
                    }
                    summaryBox.innerHTML = data.summary;
                }
            })
            .catch(error => {
                summaryBox.textContent = 'Error: Could not connect to the server.';
                thumbnailContainer.innerHTML = '';
                console.error('Error:', error);
            });
    };

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            fetchSummary();
        }
    });

    summarizeButton.addEventListener('click', fetchSummary);
});