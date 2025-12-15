# open_bim
This Project tries to read and write ifc files from bim projects.

## Features

### 1. IFC File Analyzer
A Python script that uses the ifcopenshell API to read and analyze IFC (Industry Foundation Classes) files. The script counts various BIM objects such as walls, doors, windows, slabs, beams, columns, and more.

### 2. SQL Database Query System (NEW!)
Parse IFC files into a SQLite database and query them using SQL. Perfect for answering questions like "how many of X objects are on floor Y?"

### Analyzer Features

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
- **Displays project information** and IFC schema version
- **Sorted by count** within each category for easy analysis

### SQL Query System Features

- **Parse IFC to SQLite database** - Convert IFC files into queryable SQL database
- **Structured data model** - Projects, Storeys (floors), and Products (elements)
- **Powerful queries** - Answer questions like:
  - "How many IfcWall objects are on Ground Floor?"
  - "What object types are on First Floor?"
  - "Which products are not assigned to any floor?"
- **Programmatic access** - Query via Python API or direct SQL
- **Persistent storage** - Database saved for repeated queries without re-parsing

### Installation

1. Install Python 3.6 or higher
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Usage

#### Analyzer (Console Output)

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

#### SQL Query System

1. Place your IFC file in the current directory
2. Run the demo script:

```bash
python ifc_query_demo.py
```

Or specify a file path:

```bash
python ifc_query_demo.py /path/to/your/file.ifc
```

This will:
- Parse the IFC file into a SQLite database (`ifc_data.db`)
- Display various query results
- Show examples of "how many X objects on floor Y" queries

#### Programmatic Usage

```python
from ifc_to_db import parse_ifc_to_db
from query_db import count_objects_on_floor, get_all_floors

# Parse IFC file to database
parse_ifc_to_db('your_file.ifc', 'ifc_data.db')

# Query: How many walls on Ground Floor?
count = count_objects_on_floor('IfcWall', 'Ground Floor')
print(f"Walls on Ground Floor: {count}")

# Get all floors
floors = get_all_floors('ifc_data.db')
for floor_name, elevation in floors:
    print(f"{floor_name}: {elevation}m")
```

### Example Output - Analyzer

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

============================================================
Total Products Across All Floors: 4500
============================================================
```

### Example Output - SQL Query System

```
======================================================================
IFC to SQL Database Query Demo
======================================================================

This demo shows how to parse IFC files into a SQLite database
and query for insights like 'how many of X objects are on floor Y?'

Found 1 IFC file(s) in current directory.
Using: /path/to/example.ifc

======================================================================
STEP 1: Parse IFC file to database
======================================================================

Parsing IFC file: /path/to/example.ifc
Created project: Sample Building
Created 3 storeys
Created 450 products (50 unassigned to floors)
Successfully parsed IFC file to database: ifc_data.db

======================================================================
STEP 2: Query the database
======================================================================

======================================================================
IFC DATABASE QUERY RESULTS
======================================================================

--- Project Information ---
  Name: Sample Building
  IFC Schema: IFC4
  File: /path/to/example.ifc

======================================================================
FLOOR SUMMARY
======================================================================

Floor Name                     Elevation     Objects
----------------------------------------------------------------------
Basement                            -3.50m        150
Ground Floor                         0.00m        200
First Floor                          3.50m        100
----------------------------------------------------------------------
TOTAL                                              450

======================================================================
EXAMPLE QUERIES: OBJECTS BY FLOOR
======================================================================

Showing counts for floor: Basement
----------------------------------------------------------------------
  How many IfcWalls on Basement? 45
  How many IfcDoors on Basement? 12
  How many IfcColumns on Basement? 24

All object types on Basement:
----------------------------------------------------------------------
Object Type                              Count
----------------------------------------------------------------------
IfcWall                                     45
IfcColumn                                   24
IfcPipeSegment                              20
IfcDoor                                     12
... and 5 more types

======================================================================
DATABASE LOCATION
======================================================================

Database saved to: /path/to/ifc_data.db

You can now query this database using:
  - The query_db.py module
  - Any SQLite client
  - Python with SQLAlchemy

Example query code:
----------------------------------------------------------------------
from query_db import count_objects_on_floor
count = count_objects_on_floor('IfcWall', 'Ground Floor')
print(f'Walls on Ground Floor: {count}')
======================================================================
```

### Requirements

- Python 3.6+
- ifcopenshell >= 0.7.0
- sqlalchemy >= 2.0.0 (for SQL query functionality)

## Project Files

### Core Scripts
- **`analyze_ifc.py`** - Original IFC analyzer with console output
- **`ifc_query_demo.py`** - Demo script for SQL query functionality

### SQL Query Modules
- **`db_models.py`** - SQLAlchemy database models (Project, Storey, Product)
- **`ifc_to_db.py`** - IFC parser that populates SQLite database
- **`query_db.py`** - Query functions for database operations

### Available Query Functions

```python
# From query_db module:
count_objects_on_floor(ifc_type, floor_name)      # Count specific objects on a floor
get_all_object_types_on_floor(floor_name)         # All object types on a floor
get_all_floors()                                  # List all floors with elevations
get_object_type_counts()                          # Overall object type counts
get_floor_summary()                               # Summary of all floors
get_unassigned_products()                         # Products not on any floor
get_project_info()                                # Project metadata
```

### Notes

- The script looks for files with `.ifc` or `.IFC` extensions
- Multiple IFC files in the directory will all be analyzed
- The script uses only the ifcopenshell API (no other dependencies)
