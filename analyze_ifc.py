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


def find_ifc_files():
    """Find all IFC files in the current directory."""
    ifc_files = glob.glob("*.ifc") + glob.glob("*.IFC")
    return ifc_files


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
            print(f"  Project Name: {project.Name if hasattr(project, 'Name') else 'N/A'}")
            print(f"  Description: {project.Description if hasattr(project, 'Description') and project.Description else 'N/A'}")
        
        # Define common BIM object types to count
        object_types = [
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
        
        print(f"\n{'='*60}")
        print("Object Count Summary:")
        print(f"{'='*60}\n")
        
        results = {}
        total_count = 0
        
        for obj_type in object_types:
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
    ifc_files = find_ifc_files()
    
    if not ifc_files:
        print("\nNo IFC files found in the current directory.")
        print("Please place an IFC file in the same directory as this script.")
        print("\nSupported file extensions: .ifc, .IFC")
        return 1
    
    print(f"\nFound {len(ifc_files)} IFC file(s):")
    for i, file in enumerate(ifc_files, 1):
        print(f"  {i}. {file}")
    
    # Analyze each IFC file
    for ifc_file in ifc_files:
        analyze_ifc_file(ifc_file)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
