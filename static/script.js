function searchAttendance() {
    const phoneNumber = document.getElementById('phoneInput').value.trim();
    const statusBar = document.getElementById('statusBar');
    const resultsTable = document.getElementById('resultsTable');
    const resultsBody = document.getElementById('resultsBody');

    // Validate phone number
    if (!phoneNumber) {
        statusBar.textContent = 'Please enter a phone number';
        statusBar.className = 'alert alert-warning';
        return;
    }

    statusBar.textContent = 'Searching...';
    statusBar.className = 'alert alert-info';
    resultsTable.classList.add('d-none');
    resultsBody.innerHTML = '';

    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `phone=${encodeURIComponent(phoneNumber)}`
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Received data:', data);
        if (data.error) {
            statusBar.textContent = data.error;
            statusBar.className = 'alert alert-danger';
            return;
        }

        // Check if data and records exist
        if (!data.records || !Array.isArray(data.records)) {
            throw new Error('Invalid data format received from server');
        }

        statusBar.textContent = `Found ${data.records.length} records for ${data.name}`;
        statusBar.className = 'alert alert-success';
        
        data.records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.Date || 'N/A'}</td>
                <td>${record.Time || 'N/A'}</td>
                <td>${record.Status || 'N/A'}</td>
            `;
            resultsBody.appendChild(row);
        });

        resultsTable.classList.remove('d-none');
    })
    .catch(error => {
        console.error('Search error:', error);
        console.error('Error details:', error.message);
        statusBar.textContent = 'An error occurred while searching. Please try again.';
        statusBar.className = 'alert alert-danger';
    });
}