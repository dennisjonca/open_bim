// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const categoryPanels = document.querySelectorAll('.category-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;

            // Update active tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Update active panel
            categoryPanels.forEach(panel => panel.classList.remove('active'));
            const activePanel = document.querySelector(`.category-panel[data-category="${category}"]`);
            if (activePanel) {
                activePanel.classList.add('active');
            }
        });
    });

    // Query form submission
    const queryForms = document.querySelectorAll('.query-form');
    queryForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            executeQuery(this);
        });
    });
});

function executeQuery(form) {
    const queryType = form.dataset.query;
    const formData = new FormData(form);
    
    // Build parameters object
    const params = {};
    for (let [key, value] of formData.entries()) {
        if (value) {  // Only include non-empty values
            params[key] = value;
        }
    }

    // Show loading state
    showLoading();

    // Execute query
    fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query_type: queryType,
            params: params
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            displayResults(data);
        }
    })
    .catch(error => {
        showError('Fehler beim Ausführen der Abfrage: ' + error.message);
    });
}

function showLoading() {
    const resultsSection = document.getElementById('results');
    const resultsContent = document.getElementById('results-content');
    
    resultsSection.style.display = 'block';
    resultsContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Abfrage wird ausgeführt...</p>
        </div>
    `;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function showError(message) {
    const resultsContent = document.getElementById('results-content');
    resultsContent.innerHTML = `
        <div class="alert alert-error">
            <strong>Fehler:</strong> ${message}
        </div>
    `;
}

function displayResults(data) {
    const resultsContent = document.getElementById('results-content');
    
    if (data.type === 'value') {
        resultsContent.innerHTML = createValueResult(data);
    } else if (data.type === 'table') {
        resultsContent.innerHTML = createTableResult(data);
    } else if (data.type === 'compliance') {
        resultsContent.innerHTML = createComplianceResult(data);
    } else {
        resultsContent.innerHTML = '<p>Unbekannter Ergebnistyp</p>';
    }
}

function createValueResult(data) {
    return `
        <div class="result-card">
            <div class="result-title">${data.title}</div>
            <div>
                <span class="result-value">${data.value}</span>
                <span class="result-unit">${data.unit}</span>
            </div>
        </div>
    `;
}

function createTableResult(data) {
    if (!data.data || data.data.length === 0) {
        return `
            <div class="result-card">
                <div class="result-title">${data.title}</div>
                <p>Keine Daten gefunden</p>
            </div>
        `;
    }

    let tableHTML = `
        <div class="result-card">
            <div class="result-title">${data.title}</div>
            <table class="result-table">
                <thead>
                    <tr>
    `;

    // Headers
    data.headers.forEach(header => {
        tableHTML += `<th>${header}</th>`;
    });

    tableHTML += `
                    </tr>
                </thead>
                <tbody>
    `;

    // Data rows
    data.data.forEach(row => {
        tableHTML += '<tr>';
        row.forEach(cell => {
            tableHTML += `<td>${cell}</td>`;
        });
        tableHTML += '</tr>';
    });

    tableHTML += `
                </tbody>
            </table>
        </div>
    `;

    return tableHTML;
}

function createComplianceResult(data) {
    const statusClass = data.passed ? 'passed' : 'failed';
    
    let detailsHTML = '';
    if (data.details && data.details.length > 0) {
        detailsHTML = '<ul class="compliance-details">';
        data.details.forEach(detail => {
            detailsHTML += `<li>${detail}</li>`;
        });
        detailsHTML += '</ul>';
    }

    return `
        <div class="result-card">
            <div class="result-title">${data.title}</div>
            <div class="compliance-result ${statusClass}">
                <div class="compliance-status">${data.status}</div>
                ${detailsHTML}
            </div>
        </div>
    `;
}
