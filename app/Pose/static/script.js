document.addEventListener('DOMContentLoaded', function() {
    const captureRadios = document.getElementsByName('capture');
    const uploadInput = document.getElementById('upload-input');
    const videoUpload = document.getElementById('video-upload');
    const startButton = document.getElementById('start-detection');
    const liveCamPage = document.getElementById('live-cam-page');
    const videoDisplayPage = document.getElementById('video-display-page');
    const homePage = document.getElementById('home-page');
    const exerciseSelect = document.getElementById('exercise-select');
    const liveCam = document.getElementById('live-cam');

    // Initially hide the upload input
    uploadInput.classList.add('hidden');

    // Toggle between live and upload modes
    captureRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'upload') {
                uploadInput.classList.remove('hidden');
            } else {
                uploadInput.classList.add('hidden');
            }
        });
    });

    // Start detection based on selected mode
    startButton.addEventListener('click', function() {
        const captureMode = document.querySelector('input[name="capture"]:checked').value;
        const selectedExercise = exerciseSelect.value;

        // Send selected exercise to backend
        fetch('/set_exercise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ exercise: selectedExercise }),
        });

        // Live Camera Mode
        if (captureMode === 'live') {
            homePage.classList.add('hidden');
            liveCamPage.classList.remove('hidden');
            liveCam.src = `/video_feed/${selectedExercise}`;
        } 
        // Upload Video Mode
        else if (captureMode === 'upload') {
            const videoFile = videoUpload.files[0];
            const formData = new FormData();
            formData.append('video', videoFile);

            // Upload and process video
            fetch('/upload_video', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('uploaded-video').src = data.file;
                homePage.classList.add('hidden');
                videoDisplayPage.classList.remove('hidden');
            });
        }
    });

    document.getElementById('end-detection').addEventListener('click', function() { 
        fetch('/stop_stream', {
            method: 'POST'
        }).then(response => response.json()).then(data => {
            console.log(data.status);  // Should print "stopped"
            
            // Hide the live camera page and show the home page
            document.getElementById('live-cam-page').classList.add('hidden');
            document.getElementById('home-page').classList.remove('hidden');
            
            // Optionally, clear the live camera feed
            document.getElementById('live-cam').src = '';  // Reset the camera feed
        });
    });
    

    // End video detection
    // document.getElementById('end-detection-upload').addEventListener('click', () => {
    //     videoDisplayPage.classList.add('hidden');
    //     homePage.classList.remove('hidden');
    // });
});
