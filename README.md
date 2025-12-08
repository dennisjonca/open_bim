# open_bim
This Project tries to read and write ifc files from bim projects.

## IFC File Analyzer

A Python script that uses the ifcopenshell API to read and analyze IFC (Industry Foundation Classes) files. The script counts various BIM objects such as walls, doors, windows, slabs, beams, columns, and more.

### Features

- Automatically detects IFC files in the current directory
- Reads IFC files using ifcopenshell API only
- Counts common BIM object types:
  - Walls (IfcWall, IfcWallStandardCase)
  - Doors (IfcDoor)
  - Windows (IfcWindow)
  - Slabs (IfcSlab)
  - Beams (IfcBeam)
  - Columns (IfcColumn)
  - Stairs (IfcStair)
  - Roofs (IfcRoof)
  - Spaces (IfcSpace)
  - Furniture (IfcFurnishingElement)
  - And more...
- Displays project information
- Shows IFC schema version

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

Found 1 IFC file(s):
  1. example.ifc

============================================================
Analyzing IFC file: example.ifc
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
```

### Requirements

- Python 3.6+
- ifcopenshell >= 0.7.0

### Notes

- The script looks for files with `.ifc` or `.IFC` extensions
- Multiple IFC files in the directory will all be analyzed
- The script uses only the ifcopenshell API (no other dependencies)
