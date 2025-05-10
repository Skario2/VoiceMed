const form = document.getElementById('uploadForm');
const messageDiv = document.getElementById('message');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(form);

  try {
    const response = await fetch('https://your-backend-server.com/upload', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      messageDiv.textContent = 'File uploaded successfully!';
      messageDiv.style.color = 'green';
      form.reset();
    } else {
      messageDiv.textContent = 'Upload failed. Please try again.';
      messageDiv.style.color = 'red';
    }
  } catch (error) {
    messageDiv.textContent = 'Error: ' + error.message;
    messageDiv.style.color = 'red';
  }
});
