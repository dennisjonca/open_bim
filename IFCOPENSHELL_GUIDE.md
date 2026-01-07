# IfcOpenShell Guide for This Project

## What is IfcOpenShell?

IfcOpenShell is a Python library for working with IFC (Industry Foundation Classes) files. IFC is an open standard for Building Information Modeling (BIM) data that allows different software applications to exchange building and construction industry data.

## Installation

```bash
pip install ifcopenshell
```

This project includes ifcopenshell in `requirements.txt`, so running `pip install -r requirements.txt` will install it automatically.

## Basic Usage in This Project

### 1. Opening an IFC File

```python
import ifcopenshell

# Open an IFC file
ifc_file = ifcopenshell.open('path/to/building.ifc')
```

### 2. Reading Elements by Type

The most common operation is to get all elements of a specific type:

```python
# Get all outlets in the building
outlets = ifc_file.by_type('IfcOutlet')

# Get all doors
doors = ifc_file.by_type('IfcDoor')

# Get all windows
windows = ifc_file.by_type('IfcWindow')

# Get all pipe segments
pipes = ifc_file.by_type('IfcPipeSegment')
```

### 3. Example: Reading IfcOutlets from a File

Here's a complete example showing how to read and work with IfcOutlets:

```python
import ifcopenshell

# Step 1: Open the IFC file
ifc_file = ifcopenshell.open('my_building.ifc')

# Step 2: Get all outlets
outlets = ifc_file.by_type('IfcOutlet')

print(f"Found {len(outlets)} outlets in the building")

# Step 3: Iterate through outlets and get their properties
for outlet in outlets:
    # Get basic information
    outlet_id = outlet.id()
    outlet_name = outlet.Name if hasattr(outlet, 'Name') else 'Unnamed'
    
    print(f"Outlet #{outlet_id}: {outlet_name}")
    
    # Get which floor/storey the outlet is on
    if hasattr(outlet, 'ContainedInStructure') and outlet.ContainedInStructure:
        for rel in outlet.ContainedInStructure:
            if hasattr(rel, 'RelatingStructure'):
                structure = rel.RelatingStructure
                if structure.is_a('IfcBuildingStorey'):
                    print(f"  - Located on: {structure.Name}")
```

### 4. What You Need to Read IFC Data

To successfully read IFC data, you need:

1. **An IFC File**: A valid `.ifc` file exported from BIM software (Revit, ArchiCAD, etc.)

2. **IfcOpenShell Library**: Installed via pip
   ```bash
   pip install ifcopenshell
   ```

3. **Knowledge of IFC Element Types**: Common types include:
   - `IfcOutlet` - Electrical outlets
   - `IfcSwitchingDevice` - Light switches
   - `IfcLightFixture` - Light fixtures
   - `IfcDoor` - Doors
   - `IfcWindow` - Windows
   - `IfcWall` - Walls
   - `IfcSlab` - Slabs (floors, ceilings)
   - `IfcPipeSegment` - Pipe segments
   - `IfcDuctSegment` - Duct segments
   - `IfcCableCarrierSegment` - Cable trays
   - `IfcSpace` - Spaces/rooms
   - `IfcBuildingStorey` - Building floors

4. **Understanding of IFC Relationships**: IFC uses relationships to connect elements:
   - `ContainedInStructure` - Links elements to spaces/storeys
   - `IsDefinedBy` - Links elements to properties and quantities
   - `IsGroupedBy` - Links elements to systems

## How This Project Uses IfcOpenShell

### In `ifc_queries.py`

The project uses ifcopenshell to:

1. **Count Elements**:
   ```python
   def count_by_type_total(ifc_file, element_type):
       """Count total elements of a specific type."""
       return len(ifc_file.by_type(element_type))
   ```

2. **Get Element Locations**:
   ```python
   def get_product_storey(product):
       """Get the building storey (floor) that contains a product."""
       if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
           for rel in product.ContainedInStructure:
               if hasattr(rel, 'RelatingStructure'):
                   structure = rel.RelatingStructure
                   if structure.is_a("IfcBuildingStorey"):
                       return structure.Name
   ```

3. **Extract Quantities**:
   ```python
   def get_element_length(element):
       """Get the length of a linear element."""
       if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
           for definition in element.IsDefinedBy:
               if definition.is_a('IfcRelDefinesByProperties'):
                   property_definition = definition.RelatingPropertyDefinition
                   
                   # Check IfcElementQuantity for length data
                   if property_definition.is_a('IfcElementQuantity'):
                       for quantity in property_definition.Quantities:
                           if quantity.is_a('IfcQuantityLength'):
                               if quantity.Name in ['Length', 'NominalLength']:
                                   return float(quantity.LengthValue)
   ```

### In `app.py`

The Flask application uses these query functions:

```python
# Open IFC file from upload
ifc_file = ifcopenshell.open(filepath)

# Get available element types
element_types = ifc_queries.get_available_element_types(ifc_file)

# Execute queries
counts = ifc_queries.count_by_type_and_storey(ifc_file, 'IfcOutlet')
```

## IFC Data Structure

### Hierarchy

```
IfcProject
  └─ IfcSite
      └─ IfcBuilding
          └─ IfcBuildingStorey (Floor/Level)
              └─ IfcSpace (Room)
                  └─ IfcProduct (Elements like outlets, doors, etc.)
```

### Properties and Quantities

IFC elements can have:

1. **Properties** (`IfcPropertySet`): Key-value pairs like "Manufacturer", "Model", etc.
2. **Quantities** (`IfcElementQuantity`): Measured values like length, area, volume
   - `IfcQuantityLength` - For linear elements (pipes, cables)
   - `IfcQuantityArea` - For surface elements (slabs, walls)
   - `IfcQuantityVolume` - For volumetric elements

### Example: Getting Length from IFC

```python
# Method 1: From IfcElementQuantity (standard way)
for definition in element.IsDefinedBy:
    if definition.is_a('IfcRelDefinesByProperties'):
        prop_def = definition.RelatingPropertyDefinition
        if prop_def.is_a('IfcElementQuantity'):
            for quantity in prop_def.Quantities:
                if quantity.is_a('IfcQuantityLength'):
                    length = quantity.LengthValue  # in meters

# Method 2: From IfcPropertySet (alternative)
for definition in element.IsDefinedBy:
    if definition.is_a('IfcRelDefinesByProperties'):
        prop_def = definition.RelatingPropertyDefinition
        if prop_def.is_a('IfcPropertySet'):
            for prop in prop_def.HasProperties:
                if prop.Name == 'Length':
                    length = prop.NominalValue.wrappedValue
```

## Common Tasks

### Task 1: Count All Outlets

```python
import ifcopenshell

ifc_file = ifcopenshell.open('building.ifc')
outlets = ifc_file.by_type('IfcOutlet')
print(f"Total outlets: {len(outlets)}")
```

### Task 2: Count Outlets Per Floor

```python
from collections import defaultdict

outlet_counts = defaultdict(int)

for outlet in ifc_file.by_type('IfcOutlet'):
    # Find which floor the outlet is on
    if hasattr(outlet, 'ContainedInStructure') and outlet.ContainedInStructure:
        for rel in outlet.ContainedInStructure:
            if hasattr(rel, 'RelatingStructure'):
                structure = rel.RelatingStructure
                if structure.is_a('IfcBuildingStorey'):
                    floor_name = structure.Name
                    outlet_counts[floor_name] += 1

for floor, count in outlet_counts.items():
    print(f"{floor}: {count} outlets")
```

### Task 3: Calculate Total Pipe Length

```python
total_length = 0

for pipe in ifc_file.by_type('IfcPipeSegment'):
    # Try to get length from quantities
    if hasattr(pipe, 'IsDefinedBy') and pipe.IsDefinedBy:
        for definition in pipe.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                prop_def = definition.RelatingPropertyDefinition
                if prop_def.is_a('IfcElementQuantity'):
                    for quantity in prop_def.Quantities:
                        if quantity.is_a('IfcQuantityLength'):
                            total_length += quantity.LengthValue
                            break

print(f"Total pipe length: {total_length:.2f} meters")
```

### Task 4: List All Spaces/Rooms

```python
spaces = ifc_file.by_type('IfcSpace')

for space in spaces:
    space_name = space.Name or space.LongName or f"Space #{space.id()}"
    
    # Get which floor the space is on
    floor_name = "Unknown"
    if hasattr(space, 'ContainedInStructure') and space.ContainedInStructure:
        for rel in space.ContainedInStructure:
            if hasattr(rel, 'RelatingStructure'):
                structure = rel.RelatingStructure
                if structure.is_a('IfcBuildingStorey'):
                    floor_name = structure.Name
    
    # Get area
    area = 0
    if hasattr(space, 'IsDefinedBy') and space.IsDefinedBy:
        for definition in space.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                prop_def = definition.RelatingPropertyDefinition
                if prop_def.is_a('IfcElementQuantity'):
                    for quantity in prop_def.Quantities:
                        if quantity.is_a('IfcQuantityArea'):
                            area = quantity.AreaValue
    
    print(f"{space_name} on {floor_name}: {area:.2f} m²")
```

## Troubleshooting

### Problem: "No elements found"
- **Solution**: Check that your IFC file actually contains the element type you're looking for. Use `ifc_file.by_type('IfcProduct')` to see all available products.

### Problem: "Length is 0"
- **Solution**: The IFC file may not have quantity data. Check if the element has `IfcElementQuantity` attached. Some IFC files only have geometry, not calculated quantities.

### Problem: "Elements not assigned to storey"
- **Solution**: The BIM model may not have proper spatial containment relationships. Elements need to be properly placed in spaces or storeys in the BIM authoring tool.

### Problem: "Can't find specific property"
- **Solution**: Property names vary by BIM software. Iterate through all properties to see what's available:
  ```python
  for definition in element.IsDefinedBy:
      if definition.is_a('IfcRelDefinesByProperties'):
          prop_def = definition.RelatingPropertyDefinition
          if prop_def.is_a('IfcPropertySet'):
              print(f"Property Set: {prop_def.Name}")
              for prop in prop_def.HasProperties:
                  print(f"  - {prop.Name}: {prop.NominalValue}")
  ```

## Resources

- **Official Documentation**: https://docs.ifcopenshell.org/
- **IFC Schema Reference**: https://standards.buildingsmart.org/IFC/
- **GitHub Repository**: https://github.com/IfcOpenShell/IfcOpenShell
- **Forum**: https://forum.osarch.org/

## Key Takeaways

1. IfcOpenShell provides Python access to IFC building data
2. Use `ifc_file.by_type('ElementType')` to get elements
3. Navigate relationships to find where elements are located
4. Extract quantities from `IfcElementQuantity` for length, area, volume
5. IFC data quality depends on how the BIM model was authored
6. This project uses ifcopenshell to power a web-based query interface for BIM data
