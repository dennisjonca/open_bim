#!/usr/bin/env python3
"""
IFC File Analyzer
This script reads an IFC file from the current folder and counts various BIM objects.
Uses ifcopenshell API only.
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


# Common BIM object types to count
OBJECT_TYPES = [
    "IfcWall",
    "IfcWallStandardCase",
    "IfcDoor",
    "IfcWindow",
    "IfcSlab",
    "IfcBeam",
    "IfcColumn",
    "IfcStair",
    "IfcRoof",
    "IfcSpace",
    "IfcFurnishingElement",
    "IfcBuildingElementProxy",
]


def find_ifc_files():
    """Find all IFC files in the current directory only."""
    # Get current working directory for absolute paths
    current_dir = os.getcwd()
    
    # Find IFC files in current directory only (not recursive)
    ifc_files = []
    for pattern in ["*.ifc", "*.IFC"]:
        # Use absolute path to ensure we get full paths in output
        found_files = glob.glob(os.path.join(current_dir, pattern))
        ifc_files.extend(found_files)
    
    # Remove duplicates (in case of case-insensitive filesystem)
    ifc_files = list(set(ifc_files))
    
    # Sort for consistent output
    ifc_files.sort()
    
    return ifc_files, current_dir


def analyze_ifc_file(file_path):
    """
    Analyze an IFC file and count various object types.
    
    Args:
        file_path: Path to the IFC file
        
    Returns:
        Dictionary with counts of different object types
    """
    print(f"\n{'='*60}")
    print(f"Analyzing IFC file: {file_path}")
    print(f"{'='*60}\n")
    
    try:
        # Open the IFC file
        ifc_file = ifcopenshell.open(file_path)
        
        # Get file information
        print(f"IFC Schema: {ifc_file.schema}")
        print(f"\nFile Information:")
        
        # Get project information if available
        projects = ifc_file.by_type("IfcProject")
        if projects:
            project = projects[0]
            try:
                project_name = project.Name or 'N/A'
            except (AttributeError, TypeError):
                project_name = 'N/A'
            try:
                project_desc = project.Description or 'N/A'
            except (AttributeError, TypeError):
                project_desc = 'N/A'
            print(f"  Project Name: {project_name}")
            print(f"  Description: {project_desc}")
        
        print(f"\n{'='*60}")
        print("Object Count Summary:")
        print(f"{'='*60}\n")
        
        results = {}
        total_count = 0
        
        for obj_type in OBJECT_TYPES:
            elements = ifc_file.by_type(obj_type)
            count = len(elements)
            if count > 0:
                results[obj_type] = count
                total_count += count
                print(f"  {obj_type:30s}: {count:5d}")
        
        # Also count all building elements
        all_building_elements = ifc_file.by_type("IfcBuildingElement")
        print(f"\n  {'Total IfcBuildingElement':30s}: {len(all_building_elements):5d}")
        
        # Count all products (most general geometric objects)
        all_products = ifc_file.by_type("IfcProduct")
        print(f"  {'Total IfcProduct':30s}: {len(all_products):5d}")
        
        print(f"\n{'='*60}")
        print(f"Total Specific Objects Counted: {total_count}")
        print(f"{'='*60}\n")
        
        return results
        
    except Exception as e:
        print(f"Error analyzing IFC file: {e}")
        return None


def main():
    """Main function to find and analyze IFC files."""
    print("\n" + "="*60)
    print("IFC File Analyzer using ifcopenshell")
    print("="*60)
    
    # Find IFC files in current directory
    ifc_files, current_dir = find_ifc_files()
    
    if not ifc_files:
        print("\nNo IFC files found in the current directory.")
        print("Please place an IFC file in the same directory as this script.")
        print("\nSupported file extensions: .ifc, .IFC")
        return 1
    
    print(f"\nFound {len(ifc_files)} IFC file(s) in current directory:")
    print(f"Current directory: {current_dir}\n")
    for i, file in enumerate(ifc_files, 1):
        print(f"  {i}. {file}")
    
    # Analyze each IFC file
    for ifc_file in ifc_files:
        analyze_ifc_file(ifc_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
