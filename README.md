# open_bim
This Project tries to read and write ifc files from bim projects.

## IFC Query Web Application

A Flask-based web application that allows you to upload IFC files and query them through an intuitive web interface. Answer complex questions about your BIM data without writing code.

### Features

The web application provides 9 comprehensive query categories covering all aspects of IFC data:

1. **Quantity & Cost Estimation** - Count elements per storey or building-wide
2. **Lengths & Volumes** - Calculate total lengths of pipes, ducts, cables, and surface areas
3. **Element Context** - Find elements in specific spaces or host types
4. **System Analysis** - Analyze MEP systems and electrical circuits
5. **Space & Usage** - Calculate areas and analyze space usage patterns
6. **Compliance Checking** - Verify elements are in required locations
7. **Installation Planning** - Coordinate on-site installation work
8. **Maintenance & Handover** - Locate maintainable devices and distribution points
9. **Compound Queries** - Complex queries with multiple filters

### Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

4. Upload an IFC file and start querying!

### Usage

1. **Upload IFC File**: Click "Choose IFC File" on the home page and upload your IFC file
2. **Select Query Category**: Choose from 9 categories in the sidebar
3. **Configure Query**: Fill in the form parameters for your specific question
4. **Execute Query**: Click "Execute Query" to see results
5. **View Results**: Results are displayed as tables, values, or compliance checks

### Example Queries

- "How many electrical outlets are on the ground floor?"
- "What is the total length of potable water piping?"
- "How many luminaires are installed in office spaces?"
- "Which floor has the highest installation density?"
- "Are there outlets in every office room?"

## IFC File Analyzer (Command Line)

A Python script that uses the ifcopenshell API to read and analyze IFC (Industry Foundation Classes) files. The script counts various BIM objects such as walls, doors, windows, slabs, beams, columns, and more.

### Features

- **Automatically detects IFC files** in the current directory (shows full file paths)
- **Reads IFC files** using ifcopenshell API only
- **Quick summary** of common BIM object types:
  - Walls, Doors, Windows, Slabs, Beams, Columns
  - Stairs, Roofs, Spaces, Furniture, and more
- **Comprehensive product listing** - Shows ALL IfcProduct types organized by category:
  - **Structural Elements**: Walls, beams, columns, slabs, footings, etc.
  - **MEP & HVAC**: Ducts, pipes, pumps, valves, boilers, chillers, etc.
  - **Electrical & Lighting**: Lamps, light fixtures, sensors, cables, outlets, etc.
  - **Plumbing & Sanitary**: Sanitary terminals, waste terminals, etc.
  - **Sensors & Controls**: Sensors, actuators, alarms, controllers, etc.
  - **Furnishing & Equipment**: Furniture, medical devices, audio/visual equipment, etc.
  - **Transport**: Transport elements
  - **And more categories...**
- **Floor/Storey-based organization** - Shows products sorted by building floor:
  - Displays products for each floor (Basement, Ground Floor, First Floor, etc.)
  - Sorted by elevation from lowest to highest
  - Shows elevation values for each floor
  - Includes total counts per floor and grand total
  - **Enhanced spatial relationship detection** for better storey assignment:
    - Checks `IfcRelContainedInSpatialStructure` (direct containment)
    - Checks `IfcRelReferencedInSpatialStructure` (often used for MEP/outlets)
    - Checks `IfcRelAggregates` (spatial decomposition)
    - Traverses through spaces to find parent storeys
- **Unassigned Object Analysis** - Helps diagnose why objects lack storey assignment:
  - Shows which objects have spatial relationships but no storey assignment
  - Shows which objects have no spatial relationships at all
  - Displays the types of relationships found for debugging
  - Provides recommendations for fixing assignments in BIM authoring tools
- **MEP System Organization** - Shows products organized by MEP systems:
  - Displays electrical circuits with all connected devices (outlets, fixtures, etc.)
  - Shows HVAC systems with their components (pumps, valves, terminals, etc.)
  - Lists plumbing systems and their connections
  - Identifies MEP products not assigned to any system
  - Helps understand system connectivity and organization
  - Uses `IfcSystem`, `IfcElectricalCircuit`, and `IfcDistributionSystem` relationships
- **Displays project information** and IFC schema version
- **Sorted by count** within each category for easy analysis

### Installation

1. Install Python 3.6 or higher
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Usage

1. Place your IFC file(s) in the same directory as `analyze_ifc.py`
2. Run the script:

```bash
python analyze_ifc.py
```

Or make it executable and run directly:

```bash
chmod +x analyze_ifc.py
./analyze_ifc.py
```

### Example Output

```
============================================================
IFC File Analyzer using ifcopenshell
============================================================

Found 1 IFC file(s) in current directory:
Current directory: /path/to/your/directory

  1. /path/to/your/directory/example.ifc

============================================================
Analyzing IFC file: /path/to/your/directory/example.ifc
============================================================

IFC Schema: IFC4

File Information:
  Project Name: Sample Building
  Description: Example IFC file

============================================================
Object Count Summary:
============================================================

  IfcWall                       :    45
  IfcDoor                       :    12
  IfcWindow                     :    18
  IfcSlab                       :     8
  IfcBeam                       :    24
  IfcColumn                     :    16

  Total IfcBuildingElement      :   150
  Total IfcProduct              :   180

============================================================
Total Specific Objects Counted: 123
============================================================

============================================================
All Products by Category:
============================================================

Electrical & Lighting (450 items):
------------------------------------------------------------
  IfcLightFixture                         :   300
  IfcSensor                               :   100
  IfcLamp                                 :    50

Structural Elements (125 items):
------------------------------------------------------------
  IfcBeam                                 :    80
  IfcWall                                 :    45

... (more categories) ...

============================================================
Total Products Across All Categories: 4500
============================================================

============================================================
Products by Floor/Storey:
============================================================

Basement (Elevation: -3.50m) - 234 items:
------------------------------------------------------------
  IfcWall                                 :    89
  IfcColumn                               :    45
  IfcPipeSegment                          :    45
  IfcSlab                                 :    25
  IfcPump                                 :    18
  IfcSpace                                :    12

Ground Floor (Elevation: 0.00m) - 1245 items:
------------------------------------------------------------
  IfcWall                                 :   345
  IfcFurniture                            :   234
  IfcLightFixture                         :   123
  IfcWindow                               :    89
  IfcColumn                               :    78
  IfcDoor                                 :    67
  ... (more products) ...

First Floor (Elevation: 3.50m) - 1523 items:
------------------------------------------------------------
  IfcWall                                 :   456
  IfcFurniture                            :   312
  IfcLightFixture                         :   145
  IfcWindow                               :   112
  ... (more products) ...

... (more floors) ...

Unassigned - 245 items:
------------------------------------------------------------
  IfcOutlet                               :   156
  IfcLightFixture                         :    45
  IfcSensor                               :    32
  IfcSpace                                :    12

============================================================
Total Products Across All Floors: 4500
============================================================

============================================================
Analyzing Unassigned Objects:
============================================================

Checking spatial relationships for unassigned objects...
This can help identify if objects are related to spaces that
aren't properly linked to storeys.

Objects with spatial relationships but no storey assignment:
------------------------------------------------------------
  IfcOutlet                               :   156
    → Referenced in IfcSpace
  IfcLightFixture                         :    45
    → Referenced in IfcSpace
  IfcSensor                               :    32
    → Referenced in IfcSpace

Objects with NO spatial relationships:
------------------------------------------------------------
  IfcSpace                                :    12

Recommendation:
  • Objects 'Contained in' or 'Referenced in' IfcSpace should have
    their spaces properly linked to an IfcBuildingStorey
  • Objects with no spatial relationships may need to be assigned
    to a space or storey in your BIM authoring tool
============================================================

============================================================
Products by MEP System:
============================================================

This shows how products are organized into systems such as
electrical circuits, HVAC systems, plumbing systems, etc.

Circuit A-01 (IfcElectricalCircuit) - 45 items:
------------------------------------------------------------
  IfcOutlet                               :    32
  IfcLightFixture                         :     8
  IfcSwitchingDevice                      :     5

Circuit A-02 (IfcElectricalCircuit) - 38 items:
------------------------------------------------------------
  IfcOutlet                               :    28
  IfcLightFixture                         :     7
  IfcSwitchingDevice                      :     3

HVAC Zone 1 (IfcDistributionSystem) - 156 items:
------------------------------------------------------------
  IfcAirTerminal                          :    89
  IfcDuctSegment                          :    45
  IfcDamper                               :    22

Domestic Cold Water (IfcDistributionSystem) - 67 items:
------------------------------------------------------------
  IfcPipeSegment                          :    45
  IfcValve                                :    15
  IfcSanitaryTerminal                     :     7

============================================================
Total Products in Systems: 306
============================================================

============================================================
MEP Products Not Assigned to Systems:
============================================================

Found 89 MEP products not assigned to any system:

  IfcOutlet                               :    45
  IfcLightFixture                         :    23
  IfcSensor                               :    21

Recommendation:
  • Assign MEP elements to appropriate systems in your BIM authoring tool
  • Systems help track electrical circuits, HVAC zones, plumbing networks, etc.
============================================================
```

### Requirements

- Python 3.6+
- ifcopenshell >= 0.7.0

### Notes

- The script looks for files with `.ifc` or `.IFC` extensions
- Multiple IFC files in the directory will all be analyzed
- The script uses only the ifcopenshell API (no other dependencies)
