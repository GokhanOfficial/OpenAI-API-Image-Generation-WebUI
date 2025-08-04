document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const imageForm = document.getElementById('image-form');
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const importFile = document.getElementById('import-file');
    const importBtn = document.getElementById('import-btn');
    const imagesContainer = document.getElementById('images-container');
    const noImagesMessage = document.getElementById('no-images-message');
    const loadingSection = document.getElementById('loading-section');

    // Create error message container
    const errorContainer = document.createElement('div');
    errorContainer.id = 'error-container';
    errorContainer.className = 'error-container';
    errorContainer.style.display = 'none';
    document.querySelector('.generator-section').after(errorContainer);

    // Function to show error messages
    function showError(message) {
        errorContainer.innerHTML = `
            <h3>Error</h3>
            <p>${message}</p>
        `;
        errorContainer.classList.add('show');
        
        // Hide error after 5 seconds
        setTimeout(() => {
            errorContainer.classList.remove('show');
        }, 5000);
    }

    // Handle image generation
    imageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(imageForm);
        const data = {
            prompt: formData.get('prompt'),
            model: formData.get('model'),
            n: parseInt(formData.get('n')),
            size: formData.get('size'),
            quality: formData.get('quality')
        };

        // Validate prompt
        if (!data.prompt.trim()) {
            showError('Please enter a prompt');
            return;
        }

        // Show loading indicator
        showLoading(true);

        try {
            // Send request to backend
            const response = await fetch('/generate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                // Check if we have images
                if (result.images && result.images.length > 0) {
                    // Display generated images
                    displayImages(result.images);
                    // Hide "no images" message if it exists
                    if (noImagesMessage) {
                        noImagesMessage.style.display = 'none';
                    }
                } else {
                    showError('No images were generated. Please try again with a different prompt.');
                }
            } else {
                showError('Error: ' + (result.error || 'Failed to generate images'));
            }
        } catch (error) {
            console.error('Error:', error);
            showError('An error occurred while generating images: ' + error.message);
        } finally {
            // Hide loading indicator
            showLoading(false);
        }
    });

    // Handle export session
    exportBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/export_session');
            
            if (response.ok) {
                // Create a temporary link to trigger download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `image_history_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                const result = await response.json();
                showError('Error: ' + (result.error || 'Failed to export session'));
            }
        } catch (error) {
            console.error('Error:', error);
            showError('An error occurred while exporting session: ' + error.message);
        }
    });

    // Handle import session
    importBtn.addEventListener('click', async function() {
        const file = importFile.files[0];
        
        if (!file) {
            showError('Please select a JSON file to import');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/import_session', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message);
                // Reload the page to show imported images
                location.reload();
            } else {
                showError('Error: ' + (result.error || 'Failed to import session'));
            }
        } catch (error) {
            console.error('Error:', error);
            showError('An error occurred while importing session: ' + error.message);
        }
    });

    // Function to display images
    function displayImages(images) {
        // Remove "no images" message if it exists
        if (noImagesMessage) {
            noImagesMessage.style.display = 'none';
        }

        // Add each image to the container
        images.forEach(image => {
            const imageCard = document.createElement('div');
            imageCard.className = 'image-card';
            
            imageCard.innerHTML = `
                <img src="${image.image_path}" alt="${image.prompt}">
                <div class="image-info">
                    <p><strong>Prompt:</strong> ${image.prompt}</p>
                    <p><strong>Model:</strong> ${image.model}</p>
                    <p><strong>Size:</strong> ${image.size}</p>
                    <p><strong>Quality:</strong> ${image.quality}</p>
                </div>
            `;
            
            imagesContainer.prepend(imageCard);
        });
    }

    // Function to show/hide loading indicator
    function showLoading(show) {
        if (show) {
            loadingSection.style.display = 'block';
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        } else {
            loadingSection.style.display = 'none';
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Images';
        }
    }
});
