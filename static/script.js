document.addEventListener('DOMContentLoaded', function () {
    const input = document.querySelector('.url-input');
    const summaryBox = document.querySelector('.summary-box');
    const thumbnailContainer = document.getElementById('thumbnail-container');
    const summarizeButton = document.getElementById('summarize-button');

    const fetchSummary = () => {
        const youtubeUrl = input.value.trim();
        if (!youtubeUrl) {
            summaryBox.textContent = 'Please enter a YouTube URL';
            thumbnailContainer.innerHTML = '';
            return;
        }

        summaryBox.textContent = 'Loading summary...';
        thumbnailContainer.innerHTML = '';
        summaryBox.innerHTML = '';

        const videoId = extractVideoId(youtubeUrl);
        if (!videoId) {
            summaryBox.textContent = 'Invalid YouTube URL.';
            return;
        }

        // Function to load YouTube iFrame Player API and fetch transcript
        loadYouTubeIframeAPI(videoId, (transcript) => {
            if (transcript) {
                // Send transcript and video_id to backend
                sendTranscriptToBackend(transcript, videoId);
            } else {
                summaryBox.textContent = 'Could not fetch transcript. Make sure video has captions.';
            }
        });
    };

    // Helper function to extract video ID (similar to your Python function)
    const extractVideoId = (url) => {
        const patterns = [
            /(?:v=|\/)([0-9A-Za-z_-]{11})/,
        ];
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) {
                return match[1];
            }
        }
        return null;
    };

    // Function to load YouTube iFrame Player API and fetch transcript
    const loadYouTubeIframeAPI = (videoId, callback) => {
        // Load the IFrame Player API asynchronously
        const tag = document.createElement('script');
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

        window.onYouTubeIframeAPIReady = () => {
            const player = new YT.Player('player', {
                videoId: videoId,
                events: {
                    'onReady': (event) => {
                        // Attempt to get captions after player is ready
                        try {
                            const availableLanguages = event.target.getAvailableCaptionTracks();
                            if (availableLanguages && availableLanguages.length > 0) {
                                // Select the first available caption track (you might want to allow user selection)
                                event.target.loadModule('captions');
                                event.target.setOption('captions', 'track', { languageCode: availableLanguages[0].languageCode });

                                // There's no direct API to get the full transcript text via the iFrame API.
                                // This is a limitation. A common workaround involves parsing the video page's HTML
                                // or using a different client-side library if available and permissible by YouTube's terms.
                                // *** NOTE: This part is a placeholder. Getting the *full* text transcript reliably via iFrame API is tricky. ***
                                // A robust client-side solution might require more complex methods or relying on a 3rd party client-side library.

                                // For demonstration, let's assume we *could* get the transcript text here:
                                // const transcriptText = "... fetched transcript text ...";
                                // callback(transcriptText);

                                // Since direct transcript fetching via iFrame API is limited, we'll simulate success for now
                                console.warn("Direct transcript fetching via iFrame API is limited. Simulation only.");
                                callback("Simulated Transcript for " + videoId);

                            } else {
                                console.warn("No caption tracks available for this video.");
                                callback(null);
                            }
                        } catch (e) {
                            console.error("Error getting caption tracks:", e);
                            callback(null);
                        }
                    },
                    'onError': (event) => {
                        console.error('YouTube Player Error:', event.data);
                        callback(null);
                    }
                }
            });

            // Clean up the player element after getting the transcript (optional)
            // player.destroy();
        };

        // Add a placeholder element for the YouTube player iframe
        const playerElement = document.createElement('div');
        playerElement.id = 'player';
        playerElement.style.display = 'none'; // Hide the player
        document.body.appendChild(playerElement);

    };

    // Function to send transcript and video_id to backend
    const sendTranscriptToBackend = (transcript, videoId) => {
        fetch('/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: transcript, video_id: videoId })
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