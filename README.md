# open_bim
This Project tries to read and write ifc files from bim projects.

## IFC File Analyzer

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
```

### Requirements

- Python 3.6+
- ifcopenshell >= 0.7.0

### Notes

- The script looks for files with `.ifc` or `.IFC` extensions
- Multiple IFC files in the directory will all be analyzed
- The script uses only the ifcopenshell API (no other dependencies)
