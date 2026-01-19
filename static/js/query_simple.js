// View mode and category switching functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get data passed from server
    const availableElements = window.ifcQueryData.availableElements;
    const elementTranslations = window.ifcQueryData.elementTranslations;

    // Function to get display name for an IFC element (German name / IFC name)
    function getDisplayName(ifcName) {
        let germanName = ifcName;
        let ifcTechnicalName = ifcName;
        
        // Get German name if available
        if (elementTranslations[ifcName]) {
            germanName = elementTranslations[ifcName];
        } else if (ifcName.startsWith('Ifc')) {
            germanName = ifcName.substring(3);
        }
        
        // Get IFC technical name (without 'Ifc' prefix)
        if (ifcName.startsWith('Ifc')) {
            ifcTechnicalName = ifcName.substring(3);
        }
        
        // Return format: "German name / IFC name"
        return `${germanName} / ${ifcTechnicalName}`;
    }

    // Categorize elements
    const countableElements = [];
    const linearElements = [];
    const areaElements = [];

    availableElements.forEach(elem => {
        // Add all to countable
        countableElements.push(elem);
        
        // Check if linear (pipes, ducts, cables)
        if (elem.includes('Segment') || elem.includes('Conduit')) {
            linearElements.push(elem);
        }
        
        // Check if area (slabs, coverings)
        if (elem.includes('Slab') || elem.includes('Covering') || elem.includes('Roof')) {
            areaElements.push(elem);
        }
    });

    // Populate dropdowns
    function populateSelect(selectId, elements) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // Clear existing options except first
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Add available elements with German name / IFC name format
        elements.forEach(elem => {
            const option = document.createElement('option');
            option.value = elem;
            option.textContent = getDisplayName(elem);
            select.appendChild(option);
        });
    }

    // Populate all selects
    populateSelect('quantity_storey_select', countableElements);
    populateSelect('quantity_total_select', countableElements);
    
    // Length selects
    populateSelect('length_storey_select', linearElements);
    populateSelect('length_total_select', linearElements);
    
    // Area selects
    populateSelect('area_select', areaElements);

    const viewModeButtons = document.querySelectorAll('.view-mode-button');
    const tabButtons = document.querySelectorAll('.tab-button');
    const categoryPanels = document.querySelectorAll('.category-panel');
    const viewPanels = document.querySelectorAll('.view-panel');
    const categoryTabsContainer = document.querySelector('.category-tabs');
    const categoryTabsHeading = document.querySelector('.query-sidebar h3:nth-of-type(2)');

    let currentView = 'storey';
    let currentCategory = 'quantity';

    // View mode switching
    viewModeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            currentView = view;

            // Update active button
            viewModeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Hide/show category tabs based on view mode
            if (view === 'special') {
                // Hide category tabs for special query view
                if (categoryTabsContainer) categoryTabsContainer.style.display = 'none';
                if (categoryTabsHeading) categoryTabsHeading.style.display = 'none';
            } else {
                // Show category tabs for storey view
                if (categoryTabsContainer) categoryTabsContainer.style.display = 'flex';
                if (categoryTabsHeading) categoryTabsHeading.style.display = 'block';
            }

            // Update visible panels
            updateVisiblePanels();
        });
    });

    // Category switching
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;
            currentCategory = category;

            // Update active tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Update visible panels
            updateVisiblePanels();
        });
    });

    function updateVisiblePanels() {
        if (currentView === 'special') {
            // For special view mode, show only the first category panel
            // (since all special queries are the same across categories)
            categoryPanels.forEach(panel => panel.classList.remove('active'));
            const firstCategoryPanel = document.querySelector('.category-panel[data-category="quantity"]');
            if (firstCategoryPanel) {
                firstCategoryPanel.classList.add('active');
                
                // Show the special view panel
                const categoryViewPanels = firstCategoryPanel.querySelectorAll('.view-panel');
                categoryViewPanels.forEach(panel => {
                    if (panel.dataset.view === 'special') {
                        panel.classList.add('active');
                    } else {
                        panel.classList.remove('active');
                    }
                });
            }
        } else {
            // For storey view mode, use normal category switching
            // Hide all category panels
            categoryPanels.forEach(panel => panel.classList.remove('active'));
            
            // Show the current category panel
            const activeCategory = document.querySelector(`.category-panel[data-category="${currentCategory}"]`);
            if (activeCategory) {
                activeCategory.classList.add('active');

                // Within the active category, manage view panels
                const categoryViewPanels = activeCategory.querySelectorAll('.view-panel');
                categoryViewPanels.forEach(panel => {
                    if (panel.dataset.view === currentView) {
                        panel.classList.add('active');
                    } else {
                        panel.classList.remove('active');
                    }
                });
            }
        }
    }

    // Query form submission - CRITICAL: Must be set up after DOM is ready
    const queryForms = document.querySelectorAll('.query-form');
    console.log('Setting up', queryForms.length, 'query forms');
    queryForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted:', this.dataset.query);
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
