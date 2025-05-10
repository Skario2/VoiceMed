const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('file');
const dropZone = document.getElementById('dropZone');
const messageDiv = document.getElementById('message');

// Click to trigger file dialog
dropZone.addEventListener('click', () => fileInput.click());

// Handle file selection
fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    dropZone.querySelector('p').textContent = `Selected: ${fileInput.files[0].name}`;
  }
});

// Handle drag events
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) {
    fileInput.files = e.dataTransfer.files;
    dropZone.querySelector('p').textContent = `Dropped: ${e.dataTransfer.files[0].name}`;
  }
});

// Handle upload
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  if (fileInput.files.length === 0) {
    messageDiv.textContent = 'Please select a file.';
    messageDiv.style.color = 'red';
    return;
  }

  formData.append('file', fileInput.files[0]);

  try {
    const response = await fetch('http://localhost:5000/api/upload', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    if (response.ok) {
      messageDiv.textContent = 'Upload successful: ' + result.status;
      messageDiv.style.color = 'green';
      form.reset();
      dropZone.querySelector('p').textContent = 'Drag and drop your file here or click to select';
    } else {
      messageDiv.textContent = 'Upload failed: ' + (result.error || result.status);
      messageDiv.style.color = 'red';
    }
  } catch (error) {
    messageDiv.textContent = 'Error: ' + error.message;
    messageDiv.style.color = 'red';
  }
});
