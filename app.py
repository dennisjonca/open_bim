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

# German translations for IFC element types
IFC_ELEMENT_TRANSLATIONS = {
    # Structural Elements
    'IfcWall': 'Wand',
    'IfcWallStandardCase': 'Standardwand',
    'IfcColumn': 'Stütze',
    'IfcBeam': 'Träger',
    'IfcSlab': 'Decke',
    'IfcRoof': 'Dach',
    'IfcStair': 'Treppe',
    'IfcRailing': 'Geländer',
    'IfcFooting': 'Fundament',
    'IfcPile': 'Pfahl',

    # Doors and Windows
    'IfcDoor': 'Tür',
    'IfcWindow': 'Fenster',
    'IfcCurtainWall': 'Vorhangfassade',

    # Electrical
    'IfcOutlet': 'Steckdose',
    'IfcSwitchingDevice': 'Schalter',
    'IfcLightFixture': 'Leuchte',
    'IfcLamp': 'Lampe',
    'IfcElectricDistributionBoard': 'Verteiler',
    'IfcElectricAppliance': 'Elektrisches Gerät',
    'IfcCableSegment': 'Kabelsegment',
    'IfcCableCarrierSegment': 'Kabeltrasse',
    'IfcCableFitting': 'Kabelverschraubung',
    'IfcCableCarrierFitting': 'Kabelträgerverbindung',
    'IfcJunctionBox': 'Anschlussdose',
    'IfcElectricMotor': 'Elektromotor',

    # Plumbing and HVAC
    'IfcPipeSegment': 'Rohrsegment',
    'IfcPipeFitting': 'Rohrverbindung',
    'IfcValve': 'Ventil',
    'IfcPump': 'Pumpe',
    'IfcDuctSegment': 'Lüftungskanalsegment',
    'IfcDuctFitting': 'Lüftungskanalverbindung',
    'IfcAirTerminal': 'Luftauslass',
    'IfcFan': 'Ventilator',
    'IfcDamper': 'Klappe',
    'IfcBoiler': 'Kessel',
    'IfcChiller': 'Kühler',
    'IfcHeatExchanger': 'Wärmetauscher',
    'IfcTank': 'Tank',

    # Sanitary
    'IfcSanitaryTerminal': 'Sanitärobjekt',
    'IfcWasteTerminal': 'Abfluss',

    # Sensors and Controls
    'IfcSensor': 'Sensor',
    'IfcActuator': 'Aktor',
    'IfcAlarm': 'Alarm',
    'IfcController': 'Steuergerät',
    'IfcFlowInstrument': 'Messgerät',
    'IfcUnitaryControlElement': 'Steuerelement',

    # Heating and Cooling
    'IfcSpaceHeater': 'Heizkörper',
    'IfcCooledBeam': 'Kühldecke',
    'IfcCoolingTower': 'Kühlturm',
    'IfcEvaporator': 'Verdampfer',
    'IfcCondenser': 'Kondensator',

    # Fire Protection
    'IfcFireSuppressionTerminal': 'Feuerlöscher',
    'IfcSprinkler': 'Sprinkler',

    # Furniture and Equipment
    'IfcFurniture': 'Möbel',
    'IfcSystemFurnitureElement': 'Systemmöbel',
    'IfcMedicalDevice': 'Medizinisches Gerät',

    # Space and Building
    'IfcSpace': 'Raum',
    'IfcBuildingStorey': 'Geschoss',
    'IfcBuilding': 'Gebäude',
    'IfcSite': 'Grundstück',

    # Covering
    'IfcCovering': 'Belag',
    'IfcCeiling': 'Deckenverkleidung',
    'IfcFlooring': 'Bodenbelag',
    'IfcRoofing': 'Dachdeckung',

    # Other
    'IfcTransportElement': 'Transportelement',
    'IfcPlate': 'Platte',
    'IfcMember': 'Bauteil',
    'IfcBuildingElementProxy': 'Proxy-Element',
    'IfcDistributionPort': 'Verteilungsschnittstelle',

}

def get_german_element_name(ifc_name):
    """Konvertiert IFC-Elementnamen in deutsche Bezeichnung."""
    if ifc_name in IFC_ELEMENT_TRANSLATIONS:
        return IFC_ELEMENT_TRANSLATIONS[ifc_name]
    # Fallback: Remove 'Ifc' prefix only if it starts with 'Ifc'
    if ifc_name.startswith('Ifc'):
        return ifc_name[3:]
    return ifc_name


def allowed_file(filename):
    """Prüfen, ob die Datei eine zulässige Erweiterung hat."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_ifc_file():
    """Die aktuell geladene IFC-Datei aus der Sitzung abrufen."""
    if 'ifc_filename' not in session:
        return None
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['ifc_filename'])
    if not os.path.exists(filepath):
        return None
    
    try:
        return ifcopenshell.open(filepath)
    except Exception as e:
        flash(f"Fehler beim Öffnen der IFC-Datei: {str(e)}", "error")
        return None


@app.route('/')
def index():
    """Startseite - IFC-Datei hochladen."""
    has_file = 'ifc_filename' in session
    filename = session.get('ifc_filename', '')
    return render_template('index.html', has_file=has_file, filename=filename)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Datei-Upload verarbeiten."""
    if 'file' not in request.files:
        flash('Kein Dateiteil', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Keine Datei ausgewählt', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Validieren, ob es eine gültige IFC-Datei ist
        try:
            ifc_file = ifcopenshell.open(filepath)
            session['ifc_filename'] = filename
            flash(f'Datei {filename} erfolgreich hochgeladen!', 'success')
            return redirect(url_for('query_page'))
        except Exception as e:
            os.remove(filepath)  # Ungültige Datei entfernen
            flash(f'Fehler: Keine gültige IFC-Datei - {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Ungültiger Dateityp. Bitte laden Sie eine IFC-Datei hoch.', 'error')
        return redirect(url_for('index'))


@app.route('/query')
def query_page():
    """Haupt-Abfrage-Oberfläche."""
    if 'ifc_filename' not in session:
        flash('Bitte laden Sie zuerst eine IFC-Datei hoch', 'warning')
        return redirect(url_for('index'))
    
    ifc_file = get_ifc_file()
    if not ifc_file:
        flash('Fehler beim Laden der IFC-Datei', 'error')
        return redirect(url_for('index'))
    
    # Metadaten für die Oberfläche abrufen
    storeys = ifc_queries.get_all_storeys(ifc_file)
    element_types = ifc_queries.get_available_element_types(ifc_file)
    
    return render_template('query_simple.html', 
                         filename=session['ifc_filename'],
                         storeys=storeys,
                         element_types=element_types,
                         element_translations=IFC_ELEMENT_TRANSLATIONS)


@app.route('/api/query', methods=['POST'])
def execute_query():
    """Eine Abfrage ausführen und Ergebnisse als JSON zurückgeben."""
    if 'ifc_filename' not in session:
        return jsonify({'error': 'Keine IFC-Datei geladen'}), 400
    
    ifc_file = get_ifc_file()
    if not ifc_file:
        return jsonify({'error': 'Fehler beim Laden der IFC-Datei'}), 500
    
    data = request.get_json()
    query_type = data.get('query_type')
    params = data.get('params', {})
    
    try:
        result = execute_query_type(ifc_file, query_type, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def execute_query_type(ifc_file, query_type, params):
    """Spezifische Abfrage basierend auf Typ ausführen."""
    
    # Kategorie 1: Mengen & Kostenermittlung
    if query_type == 'count_by_storey':
        element_type = params.get('element_type', 'IfcOutlet')
        counts = ifc_queries.count_by_type_and_storey(ifc_file, element_type)
        # Nach Höhe sortieren (Keller bis Dachgeschoss)
        sorted_data = ifc_queries.sort_storey_data(ifc_file, counts)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'table',
            'title': f'{german_name} Anzahl nach Geschoss',
            'headers': ['Geschoss', 'Anzahl'],
            'data': sorted_data
        }
    
    elif query_type == 'count_total':
        element_type = params.get('element_type', 'IfcDoor')
        count = ifc_queries.count_by_type_total(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'value',
            'title': f'Gesamt {german_name} Anzahl',
            'value': count,
            'unit': 'Elemente'
        }
    
    # Kategorie 2: Längen & Volumen
    elif query_type == 'total_length':
        element_type = params.get('element_type', 'IfcPipeSegment')
        length = ifc_queries.get_total_length_by_type(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'value',
            'title': f'Gesamtlänge von {german_name}',
            'value': round(length, 2),
            'unit': 'Meter'
        }
    
    elif query_type == 'length_by_storey':
        element_type = params.get('element_type', 'IfcPipeSegment')
        lengths = ifc_queries.get_length_by_storey(ifc_file, element_type)
        # Nach Höhe sortieren und Werte runden
        sorted_data = ifc_queries.sort_storey_data(ifc_file, lengths)
        sorted_data = [[name, round(length, 2)] for name, length in sorted_data]
        german_name = get_german_element_name(element_type)
        return {
            'type': 'table',
            'title': f'{german_name} Länge nach Geschoss',
            'headers': ['Geschoss', 'Länge (m)'],
            'data': sorted_data
        }
    
    elif query_type == 'length_by_system':
        element_type = params.get('element_type', 'IfcPipeSegment')
        lengths = ifc_queries.get_length_by_system(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'table',
            'title': f'{german_name} Länge nach System',
            'headers': ['System', 'Länge (m)'],
            'data': [[k, round(v, 2)] for k, v in lengths.items()]
        }
    
    elif query_type == 'total_area':
        element_type = params.get('element_type', 'IfcCovering')
        area = ifc_queries.get_total_area_by_type(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'value',
            'title': f'Gesamtfläche von {german_name}',
            'value': round(area, 2),
            'unit': 'm²'
        }
    
    # Kategorie 3: Element-Kontext-Fragen
    elif query_type == 'elements_by_host':
        element_type = params.get('element_type', 'IfcDoor')
        host_type = params.get('host_type', 'IfcWall')
        count = ifc_queries.count_elements_by_host_type(ifc_file, element_type, host_type)
        german_element = get_german_element_name(element_type)
        german_host = get_german_element_name(host_type)
        return {
            'type': 'value',
            'title': f'{german_element} in {german_host}',
            'value': count,
            'unit': 'Elemente'
        }
    
    elif query_type == 'elements_in_space_type':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        count = ifc_queries.count_elements_in_space_type(ifc_file, element_type, space_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'value',
            'title': f'{german_name} in {space_type} Räumen',
            'value': count,
            'unit': 'Elemente'
        }
    
    elif query_type == 'elements_per_space':
        element_type = params.get('element_type', 'IfcSwitchingDevice')
        counts = ifc_queries.count_elements_per_space(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'table',
            'title': f'{german_name} pro Raum',
            'headers': ['Raum', 'Anzahl'],
            'data': sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
        }
    
    # Kategorie 4: Systembasierte Fragen
    elif query_type == 'elements_by_system':
        system_name = params.get('system_name', '')
        systems = ifc_queries.get_elements_by_system(ifc_file, system_name if system_name else None)
        
        # Für Anzeige flach machen und Elementtypen übersetzen
        data = []
        for sys_name, elements in systems.items():
            for elem_type, count in elements.items():
                german_elem = get_german_element_name(elem_type)
                data.append([sys_name, german_elem, count])
        
        return {
            'type': 'table',
            'title': 'Elemente nach System',
            'headers': ['System', 'Elementtyp', 'Anzahl'],
            'data': data
        }
    
    elif query_type == 'elements_per_circuit':
        element_type = params.get('element_type', 'IfcOutlet')
        circuits = ifc_queries.count_elements_per_circuit(ifc_file, element_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'table',
            'title': f'{german_name} pro Stromkreis',
            'headers': ['Stromkreis', 'Anzahl'],
            'data': [[k, v] for k, v in circuits.items()]
        }
    
    # Kategorie 5: Raum & Nutzungsanalyse
    elif query_type == 'count_rooms':
        count = ifc_queries.count_rooms(ifc_file)
        return {
            'type': 'value',
            'title': 'Gesamtanzahl der Räume',
            'value': count,
            'unit': 'Räume'
        }
    
    elif query_type == 'net_area_per_storey':
        areas = ifc_queries.get_net_area_per_storey(ifc_file)
        # Nach Höhe sortieren und Werte runden
        sorted_data = ifc_queries.sort_storey_data(ifc_file, areas)
        sorted_data = [[name, round(area, 2)] for name, area in sorted_data]
        return {
            'type': 'table',
            'title': 'Nettofläche pro Geschoss',
            'headers': ['Geschoss', 'Fläche (m²)'],
            'data': sorted_data
        }
    
    elif query_type == 'area_by_space_type':
        space_type = params.get('space_type', 'Office')
        area = ifc_queries.get_area_by_space_type(ifc_file, space_type)
        return {
            'type': 'value',
            'title': f'Gesamtfläche der {space_type} Räume',
            'value': round(area, 2),
            'unit': 'm²'
        }
    
    elif query_type == 'elements_per_area':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        density = ifc_queries.count_elements_per_area(ifc_file, element_type, space_type)
        german_name = get_german_element_name(element_type)
        return {
            'type': 'value',
            'title': f'{german_name} pro m² in {space_type}',
            'value': round(density, 3),
            'unit': 'Elemente/m²'
        }
    
    # Kategorie 6: Konformität & Prüfung
    elif query_type == 'check_elements_in_spaces':
        element_type = params.get('element_type', 'IfcOutlet')
        space_type = params.get('space_type', 'Office')
        result = ifc_queries.check_elements_in_all_spaces(ifc_file, element_type, space_type)
        german_name = get_german_element_name(element_type)
        
        status = "✓ Alle Räume haben Elemente" if result['all_have'] else "✗ Einigen Räumen fehlen Elemente"
        
        return {
            'type': 'compliance',
            'title': f'Prüfung: {german_name} in allen {space_type} Räumen',
            'status': status,
            'passed': result['all_have'],
            'details': [
                f"Gesamt {space_type} Räume: {result['total_spaces']}",
                f"Räume mit {german_name}: {result['spaces_with_elements']}",
                f"Räume ohne {german_name}: {result['missing_count']}"
            ]
        }
    
    # Kategorie 7: Installations- & Ausführungsplanung
    elif query_type == 'elements_per_floor':
        counts = ifc_queries.count_elements_per_floor(ifc_file)
        return {
            'type': 'table',
            'title': 'Gesamtelemente pro Geschoss',
            'headers': ['Geschoss', 'Anzahl'],
            'data': sorted([[k, v] for k, v in counts.items()], key=lambda x: x[1], reverse=True)
        }
    
    elif query_type == 'highest_density_floor':
        element_type = params.get('element_type', None)
        floor, count = ifc_queries.get_floor_with_highest_density(ifc_file, element_type)
        
        title = f'Geschoss mit höchster Dichte'
        if element_type:
            german_name = get_german_element_name(element_type)
            title += f' ({german_name})'
        
        return {
            'type': 'value',
            'title': title,
            'value': f"{floor}: {count} Elemente",
            'unit': ''
        }
    
    elif query_type == 'rooms_with_most_devices':
        element_types = params.get('element_types', ['IfcOutlet', 'IfcSwitchingDevice', 'IfcLightFixture'])
        rooms = ifc_queries.get_rooms_with_most_devices(ifc_file, element_types)
        
        return {
            'type': 'table',
            'title': f'Räume mit den meisten Geräten',
            'headers': ['Raum', 'Geräteanzahl'],
            'data': rooms[:20]  # Top 20 Räume
        }
    
    # Kategorie 8: Wartung & Übergabe
    elif query_type == 'count_maintainable':
        count = ifc_queries.count_maintainable_devices(ifc_file)
        return {
            'type': 'value',
            'title': 'Gesamtzahl wartbarer Geräte',
            'value': count,
            'unit': 'Geräte'
        }
    
    elif query_type == 'locate_distribution_boards':
        locations = ifc_queries.locate_distribution_boards(ifc_file)
        return {
            'type': 'table',
            'title': 'Standorte der Verteiler',
            'headers': ['Name', 'Geschoss', 'Raum'],
            'data': [[loc['name'], loc['storey'], loc['space']] for loc in locations]
        }
    
    # Kategorie 9: Hochwertige zusammengesetzte Fragen
    elif query_type == 'filtered_count':
        element_type = params.get('element_type', 'IfcOutlet')
        storey_filter = params.get('storey_filter', None)
        space_type_filter = params.get('space_type_filter', None)
        
        count = ifc_queries.count_elements_filtered(
            ifc_file, element_type, storey_filter, space_type_filter
        )
        
        german_name = get_german_element_name(element_type)
        filters = []
        if storey_filter:
            filters.append(f"auf {storey_filter}")
        if space_type_filter:
            filters.append(f"in {space_type_filter} Räumen")
        
        filter_str = " ".join(filters) if filters else "gesamt"
        
        return {
            'type': 'value',
            'title': f'{german_name} {filter_str}',
            'value': count,
            'unit': 'Elemente'
        }
    
    else:
        return {'error': f'Unbekannter Abfragetyp: {query_type}'}


@app.route('/clear')
def clear_session():
    """Die aktuelle Sitzung und hochgeladene Datei löschen."""
    if 'ifc_filename' in session:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['ifc_filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        session.pop('ifc_filename', None)
    
    flash('Sitzung gelöscht', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # For development only - use a proper WSGI server (gunicorn, uwsgi) in production
    # Set debug=False in production environments
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
