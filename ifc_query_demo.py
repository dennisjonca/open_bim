#!/usr/bin/env python3
"""
IFC Query Demo - Demonstrates SQL query functionality for IFC data.

This script shows how to:
1. Parse an IFC file into a SQLite database
2. Query the database for various insights
3. Answer questions like "how many of X objects are on floor Y?"
"""
import os
import sys
import glob

try:
    import ifcopenshell
except ImportError:
    print("\nError: ifcopenshell is not installed.")
    print("Please install it using: pip install ifcopenshell")
    print("Or install all requirements: pip install -r requirements.txt\n")
    sys.exit(1)

try:
    from sqlalchemy import __version__ as sqlalchemy_version
except ImportError:
    print("\nError: sqlalchemy is not installed.")
    print("Please install it using: pip install sqlalchemy")
    print("Or install all requirements: pip install -r requirements.txt\n")
    sys.exit(1)

from ifc_to_db import parse_ifc_to_db
from query_db import (
    count_objects_on_floor,
    get_all_object_types_on_floor,
    get_all_floors,
    get_object_type_counts,
    get_floor_summary,
    get_unassigned_products,
    get_project_info
)


def find_ifc_files():
    """Find all IFC files in the current directory."""
    current_dir = os.getcwd()
    ifc_files = []
    for pattern in ["*.ifc", "*.IFC"]:
        found_files = glob.glob(os.path.join(current_dir, pattern))
        ifc_files.extend(found_files)
    ifc_files = list(set(ifc_files))
    ifc_files.sort()
    return ifc_files


def display_query_results(db_path='ifc_data.db'):
    """Display various query results from the database."""
    
    print("\n" + "="*70)
    print("IFC DATABASE QUERY RESULTS")
    print("="*70)
    
    # Project info
    print("\n--- Project Information ---")
    project_info = get_project_info(db_path)
    if project_info:
        print(f"  Name: {project_info['name']}")
        print(f"  IFC Schema: {project_info['ifc_schema']}")
        print(f"  File: {project_info['file_path']}")
        if project_info['description']:
            print(f"  Description: {project_info['description']}")
    
    # Floor summary
    print("\n" + "="*70)
    print("FLOOR SUMMARY")
    print("="*70)
    floors = get_floor_summary(db_path)
    if floors:
        print(f"\n{'Floor Name':<30} {'Elevation':>12} {'Objects':>10}")
        print("-"*70)
        for floor_name, elevation, count in floors:
            elev_str = f"{elevation:.2f}m" if elevation is not None else "N/A"
            print(f"{floor_name:<30} {elev_str:>12} {count:>10}")
        print("-"*70)
        total_objects = sum(count for _, _, count in floors)
        print(f"{'TOTAL':<30} {' ':>12} {total_objects:>10}")
    else:
        print("No floors found in database.")
    
    # Overall object type counts
    print("\n" + "="*70)
    print("OVERALL OBJECT TYPE COUNTS")
    print("="*70)
    object_counts = get_object_type_counts(db_path)
    if object_counts:
        print(f"\n{'Object Type':<40} {'Count':>10}")
        print("-"*70)
        for obj_type, count in object_counts[:20]:  # Show top 20
            print(f"{obj_type:<40} {count:>10}")
        if len(object_counts) > 20:
            remaining = sum(count for _, count in object_counts[20:])
            print(f"{'... and ' + str(len(object_counts) - 20) + ' more types':<40} {remaining:>10}")
    
    # Example queries: Objects per floor
    print("\n" + "="*70)
    print("EXAMPLE QUERIES: OBJECTS BY FLOOR")
    print("="*70)
    
    all_floors = get_all_floors(db_path)
    if all_floors and object_counts:
        # Pick a floor and some common object types to demonstrate
        example_floor = all_floors[0][0]  # First floor
        common_types = ['IfcWall', 'IfcDoor', 'IfcWindow', 'IfcColumn', 'IfcBeam', 'IfcSlab']
        
        print(f"\nShowing counts for floor: {example_floor}")
        print("-"*70)
        
        for obj_type in common_types:
            count = count_objects_on_floor(obj_type, example_floor, db_path)
            if count > 0:
                print(f"  How many {obj_type}s on {example_floor}? {count}")
        
        # Show all objects on this floor
        print(f"\nAll object types on {example_floor}:")
        print("-"*70)
        floor_objects = get_all_object_types_on_floor(example_floor, db_path)
        if floor_objects:
            print(f"{'Object Type':<40} {'Count':>10}")
            print("-"*70)
            for obj_type, count in floor_objects[:15]:  # Top 15
                print(f"{obj_type:<40} {count:>10}")
            if len(floor_objects) > 15:
                print(f"... and {len(floor_objects) - 15} more types")
    
    # Unassigned products
    print("\n" + "="*70)
    print("UNASSIGNED PRODUCTS (Not assigned to any floor)")
    print("="*70)
    unassigned = get_unassigned_products(db_path)
    if unassigned:
        print(f"\n{'Object Type':<40} {'Count':>10}")
        print("-"*70)
        for obj_type, count in unassigned[:10]:
            print(f"{obj_type:<40} {count:>10}")
        if len(unassigned) > 10:
            remaining = sum(count for _, count in unassigned[10:])
            print(f"{'... and ' + str(len(unassigned) - 10) + ' more types':<40} {remaining:>10}")
    else:
        print("\nAll products are assigned to floors!")
    
    print("\n" + "="*70)


def main():
    """Main function."""
    print("\n" + "="*70)
    print("IFC to SQL Database Query Demo")
    print("="*70)
    print("\nThis demo shows how to parse IFC files into a SQLite database")
    print("and query for insights like 'how many of X objects are on floor Y?'")
    
    # Find IFC files
    ifc_files = find_ifc_files()
    
    if not ifc_files:
        print("\n" + "="*70)
        print("NO IFC FILES FOUND")
        print("="*70)
        print("\nNo IFC files found in the current directory.")
        print("To use this demo:")
        print("  1. Place an IFC file in this directory")
        print("  2. Run this script again")
        print("\nSupported extensions: .ifc, .IFC")
        print("\nAlternatively, you can parse a specific file:")
        print("  python ifc_query_demo.py <path-to-ifc-file>")
        return 1
    
    # Use command line argument or first found file
    if len(sys.argv) > 1:
        ifc_file_path = sys.argv[1]
        if not os.path.exists(ifc_file_path):
            print(f"\nError: File not found: {ifc_file_path}")
            return 1
    else:
        ifc_file_path = ifc_files[0]
        print(f"\nFound {len(ifc_files)} IFC file(s) in current directory.")
        print(f"Using: {ifc_file_path}")
        if len(ifc_files) > 1:
            print(f"\nNote: To use a different file, run:")
            print(f"  python ifc_query_demo.py <path-to-ifc-file>")
    
    # Database path
    db_path = 'ifc_data.db'
    
    print("\n" + "="*70)
    print("STEP 1: Parse IFC file to database")
    print("="*70)
    
    # Parse IFC to database
    project = parse_ifc_to_db(ifc_file_path, db_path)
    
    if not project:
        print("\nFailed to parse IFC file.")
        return 1
    
    print("\n" + "="*70)
    print("STEP 2: Query the database")
    print("="*70)
    
    # Display query results
    display_query_results(db_path)
    
    print("\n" + "="*70)
    print("DATABASE LOCATION")
    print("="*70)
    print(f"\nDatabase saved to: {os.path.abspath(db_path)}")
    print("\nYou can now query this database using:")
    print("  - The query_db.py module")
    print("  - Any SQLite client")
    print("  - Python with SQLAlchemy")
    
    print("\nExample query code:")
    print("-"*70)
    print("from query_db import count_objects_on_floor")
    print("count = count_objects_on_floor('IfcWall', 'Ground Floor')")
    print(f"print(f'Walls on Ground Floor: {{count}}')")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
