#!/usr/bin/env python3
"""
Flask Web Application for IFC Data Query
Allows users to upload IFC files and query them using a web interface.
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import ifcopenshell

# Import our query functions
import ifc_queries

# Get the directory where this script is located
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask with explicit paths for templates and static files
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

# Use environment variable for secret key, generate random one if not set
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

ALLOWED_EXTENSIONS = {'ifc', 'IFC'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_ifc_file():
    """Get the currently loaded IFC file from session."""
    if 'ifc_filename' not in session:
        return None
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['ifc_filename'])
    if not os.path.exists(filepath):
        return None
    
    try:
        return ifcopenshell.open(filepath)
    except Exception as e:
        flash(f"Error opening IFC file: {str(e)}", "error")
        return None


@app.route('/')
def index():
    """Home page - upload IFC file."""
    has_file = 'ifc_filename' in session
    filename = session.get('ifc_filename', '')
    return render_template('index.html', has_file=has_file, filename=filename)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Validate it's a valid IFC file
        try:
            ifc_file = ifcopenshell.open(filepath)
            session['ifc_filename'] = filename
            flash(f'File {filename} uploaded successfully!', 'success')
            return redirect(url_for('query_page'))
        except Exception as e:
            os.remove(filepath)  # Remove invalid file
            flash(f'Error: Not a valid IFC file - {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload an IFC file.', 'error')
        return redirect(url_for('index'))


@app.route('/query')
def query_page():
    """Main query interface page."""
    if 'ifc_filename' not in session:
        flash('Please upload an IFC file first', 'warning')
        return redirect(url_for('index'))
    
    ifc_file = get_ifc_file()
    if not ifc_file:
        flash('Error loading IFC file', 'error')
        return redirect(url_for('index'))
    
    # Get metadata for the interface
    storeys = ifc_queries.get_all_storeys(ifc_file)
    element_types = ifc_queries.get_available_element_types(ifc_file)
    
    return render_template('query_simple.html', 
                         filename=session['ifc_filename'],
                         storeys=storeys,
                         element_types=element_types)


@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute a query and return results as JSON."""
    if 'ifc_filename' not in session:
        return jsonify({'error': 'No IFC file loaded'}), 400
    
    ifc_file = get_ifc_file()
    if not ifc_file:
        return jsonify({'error': 'Error loading IFC file'}), 500
    
    data = request.get_json()
    query_type = data.get('query_type')
    params = data.get('params', {})
    
    try:
        result = execute_query_type(ifc_file, query_type, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def execute_query_type(ifc_file, query_type, params):
    """Execute specific query based on type."""
    
    # Category 1: Quantity & Cost Estimation
    if query_type == 'count_by_storey':
        element_type = params.get('element_type', 'IfcOutlet')
        counts = ifc_queries.count_by_type_and_storey(ifc_file, element_type)
        return {
            'type': 'table',
            'title': f'{element_type} Count by Storey',
            'headers': ['Storey', 'Count'],
            'data': [[k, v] for k, v in counts.items()]
        }
    
    elif query_type == 'count_total':
        element_type = params.get('element_type', 'IfcDoor')
        count = ifc_queries.count_by_type_total(ifc_file, element_type)
        return {
            'type': 'value',
            'title': f'Total {element_type} Count',
            'value': count,
            'unit': 'items'
        }
    
    # Category 2: Lengths & Volumes
    elif query_type == 'total_length':
        element_type = params.get('element_type', 'IfcPipeSegment')
        length = ifc_queries.get_total_length_by_type(ifc_file, element_type)
        return {
            'type': 'value',
            'title': f'Total Length of {element_type}',
            'value': round(length, 2),
            'unit': 'meters'
        }
    
    elif query_type == 'length_by_storey':
        element_type = params.get('element_type', 'IfcPipeSegment')
        lengths = ifc_queries.get_length_by_storey(ifc_file, element_type)
        return {
            'type': 'table',
            'title': f'{element_type} Length by Storey',
            'headers': ['Storey', 'Length (m)'],
            'data': [[k, round(v, 2)] for k, v in lengths.items()]
        }
    
    elif query_type == 'length_by_system':
        element_type = params.get('element_type', 'IfcPipeSegment')
        lengths = ifc_queries.get_length_by_system(ifc_file, element_type)
        return {
            'type': 'table',
            'title': f'{element_type} Length by System',
            'headers': ['System', 'Length (m)'],
            'data': [[k, round(v, 2)] for k, v in lengths.items()]
        }
    
    elif query_type == 'total_area':
        element_type = params.get('element_type', 'IfcCovering')
        area = ifc_queries.get_total_area_by_type(ifc_file, element_type)
        return {
            'type': 'value',
            'title': f'Total Area of {element_type}',
            'value': round(area, 2),
            'unit': 'm²'
        }
    
    # Category 3: Element-Context Questions
    elif query_type == 'elements_by_host':
        element_type = params.get('element_type', 'IfcDoor')
        host_type = params.get('host_type', 'IfcWall')
        count = ifc_queries.count_elements_by_host_type(ifc_file, element_type, host_type)
        return {
            'type': 'value',
            'title': f'{element_type} in {host_type}',
            'value': count,
            'unit': 'items'
        }
    
    elif query_type == 'elements_in_space_type':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        count = ifc_queries.count_elements_in_space_type(ifc_file, element_type, space_type)
        return {
            'type': 'value',
            'title': f'{element_type} in {space_type} spaces',
            'value': count,
            'unit': 'items'
        }
    
    elif query_type == 'elements_per_space':
        element_type = params.get('element_type', 'IfcSwitchingDevice')
        counts = ifc_queries.count_elements_per_space(ifc_file, element_type)
        return {
            'type': 'table',
            'title': f'{element_type} per Space',
            'headers': ['Space', 'Count'],
            'data': sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
        }
    
    # Category 4: System-based Questions
    elif query_type == 'elements_by_system':
        system_name = params.get('system_name', '')
        systems = ifc_queries.get_elements_by_system(ifc_file, system_name if system_name else None)
        
        # Flatten for display
        data = []
        for sys_name, elements in systems.items():
            for elem_type, count in elements.items():
                data.append([sys_name, elem_type, count])
        
        return {
            'type': 'table',
            'title': 'Elements by System',
            'headers': ['System', 'Element Type', 'Count'],
            'data': data
        }
    
    elif query_type == 'elements_per_circuit':
        element_type = params.get('element_type', 'IfcOutlet')
        circuits = ifc_queries.count_elements_per_circuit(ifc_file, element_type)
        return {
            'type': 'table',
            'title': f'{element_type} per Circuit',
            'headers': ['Circuit', 'Count'],
            'data': [[k, v] for k, v in circuits.items()]
        }
    
    # Category 5: Space & Usage Analysis
    elif query_type == 'count_rooms':
        count = ifc_queries.count_rooms(ifc_file)
        return {
            'type': 'value',
            'title': 'Total Number of Rooms',
            'value': count,
            'unit': 'rooms'
        }
    
    elif query_type == 'net_area_per_storey':
        areas = ifc_queries.get_net_area_per_storey(ifc_file)
        return {
            'type': 'table',
            'title': 'Net Area per Storey',
            'headers': ['Storey', 'Area (m²)'],
            'data': [[k, round(v, 2)] for k, v in areas.items()]
        }
    
    elif query_type == 'area_by_space_type':
        space_type = params.get('space_type', 'Office')
        area = ifc_queries.get_area_by_space_type(ifc_file, space_type)
        return {
            'type': 'value',
            'title': f'Total Area of {space_type} Spaces',
            'value': round(area, 2),
            'unit': 'm²'
        }
    
    elif query_type == 'elements_per_area':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        density = ifc_queries.count_elements_per_area(ifc_file, element_type, space_type)
        return {
            'type': 'value',
            'title': f'{element_type} per m² in {space_type}',
            'value': round(density, 3),
            'unit': 'items/m²'
        }
    
    # Category 6: Compliance & Checking
    elif query_type == 'check_elements_in_spaces':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        result = ifc_queries.check_elements_in_all_spaces(ifc_file, element_type, space_type)
        
        status = "✓ All spaces have elements" if result['all_have'] else "✗ Some spaces missing elements"
        
        return {
            'type': 'compliance',
            'title': f'Check: {element_type} in all {space_type} spaces',
            'status': status,
            'passed': result['all_have'],
            'details': [
                f"Total {space_type} spaces: {result['total_spaces']}",
                f"Spaces with {element_type}: {result['spaces_with_elements']}",
                f"Spaces missing {element_type}: {result['missing_count']}"
            ]
        }
    
    # Category 7: Installation & Execution Planning
    elif query_type == 'elements_per_floor':
        counts = ifc_queries.count_elements_per_floor(ifc_file)
        return {
            'type': 'table',
            'title': 'Total Elements per Floor',
            'headers': ['Floor', 'Count'],
            'data': sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
        }
    
    elif query_type == 'highest_density_floor':
        element_type = params.get('element_type', None)
        floor, count = ifc_queries.get_floor_with_highest_density(ifc_file, element_type)
        
        title = f'Floor with Highest Density'
        if element_type:
            title += f' ({element_type})'
        
        return {
            'type': 'value',
            'title': title,
            'value': f"{floor}: {count} items",
            'unit': ''
        }
    
    elif query_type == 'rooms_with_most_devices':
        element_types = params.get('element_types', ['IfcOutlet', 'IfcSwitchingDevice', 'IfcLightFixture'])
        rooms = ifc_queries.get_rooms_with_most_devices(ifc_file, element_types)
        
        return {
            'type': 'table',
            'title': f'Rooms with Most Devices',
            'headers': ['Room', 'Device Count'],
            'data': rooms[:20]  # Top 20 rooms
        }
    
    # Category 8: Maintenance & Handover
    elif query_type == 'count_maintainable':
        count = ifc_queries.count_maintainable_devices(ifc_file)
        return {
            'type': 'value',
            'title': 'Total Maintainable Devices',
            'value': count,
            'unit': 'devices'
        }
    
    elif query_type == 'locate_distribution_boards':
        locations = ifc_queries.locate_distribution_boards(ifc_file)
        return {
            'type': 'table',
            'title': 'Distribution Board Locations',
            'headers': ['Name', 'Storey', 'Space'],
            'data': [[loc['name'], loc['storey'], loc['space']] for loc in locations]
        }
    
    # Category 9: High-value Compound Questions
    elif query_type == 'filtered_count':
        element_type = params.get('element_type', 'IfcOutlet')
        storey_filter = params.get('storey_filter', None)
        space_type_filter = params.get('space_type_filter', None)
        
        count = ifc_queries.count_elements_filtered(
            ifc_file, element_type, storey_filter, space_type_filter
        )
        
        filters = []
        if storey_filter:
            filters.append(f"on {storey_filter}")
        if space_type_filter:
            filters.append(f"in {space_type_filter} spaces")
        
        filter_str = " ".join(filters) if filters else "total"
        
        return {
            'type': 'value',
            'title': f'{element_type} {filter_str}',
            'value': count,
            'unit': 'items'
        }
    
    else:
        return {'error': f'Unknown query type: {query_type}'}


@app.route('/clear')
def clear_session():
    """Clear the current session and uploaded file."""
    if 'ifc_filename' in session:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['ifc_filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        session.pop('ifc_filename', None)
    
    flash('Session cleared', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # For development only - use a proper WSGI server (gunicorn, uwsgi) in production
    # Set debug=False in production environments
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
