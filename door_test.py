#!/usr/bin/env python3
"""
Door-Wall Type Analysis Program
================================

This script analyzes doors in an IFC file and groups them by their surrounding
wall types, with a focus on plasterboard (GKB - Gipskarton) walls.

The program detects:
- All doors (IfcDoor) in the IFC file
- The wall type that contains each door
- Special focus on GKB (plasterboard/drywall) walls

Usage:
    python door_test.py [path_to_ifc_file]
    
If no file is specified, it will search for IFC files in the current directory.
"""

import os
import sys
import glob
import traceback
from collections import defaultdict

try:
    import ifcopenshell
except ImportError:
    print("\nError: ifcopenshell is not installed.")
    print("Please install it using: pip install ifcopenshell")
    print("Or install all requirements: pip install -r requirements.txt\n")
    sys.exit(1)


# Wall type constants
WALL_TYPE_GKB = 'GKB'
WALL_TYPE_CONCRETE = 'Concrete'
WALL_TYPE_BRICK = 'Brick'
WALL_TYPE_WOOD = 'Wood'
WALL_TYPE_UNKNOWN = 'Unknown'

# Keyword constants for wall type detection
GKB_KEYWORDS = [
    # German keywords
    'gkb',
    'gipskarton',
    'gipswand',
    'trockenbau',
    'trockenbauwand',
    # English keywords
    'drywall',
    'plasterboard',
    'gypsum board',
    'gypsum wall',
]

CONCRETE_KEYWORDS = ['beton', 'concrete', 'stahlbeton']
BRICK_KEYWORDS = ['ziegel', 'brick', 'mauerwerk', 'masonry', 'stein']
WOOD_KEYWORDS = ['holz', 'wood', 'timber']


def find_ifc_files():
    """Find all IFC files in the current directory."""
    current_dir = os.getcwd()
    ifc_files = []
    
    for pattern in ["*.ifc", "*.IFC"]:
        found_files = glob.glob(os.path.join(current_dir, pattern))
        ifc_files.extend(found_files)
    
    # Remove duplicates and sort
    ifc_files = sorted(list(set(ifc_files)))
    return ifc_files


def get_element_name(element):
    """Get a displayable name for an element."""
    name = element.Name if hasattr(element, 'Name') and element.Name else None
    if not name:
        name = element.LongName if hasattr(element, 'LongName') and element.LongName else None
    if not name:
        name = f"Element #{element.id()}"
    return name


def get_element_type_name(element):
    """Get the type name of an element if it exists."""
    try:
        if hasattr(element, 'IsTypedBy') and element.IsTypedBy:
            for rel in element.IsTypedBy:
                if hasattr(rel, 'RelatingType'):
                    type_obj = rel.RelatingType
                    type_name = type_obj.Name if hasattr(type_obj, 'Name') and type_obj.Name else None
                    return type_name
    except Exception:
        pass
    return None


def get_element_type_description(element):
    """Get the description of an element's type if it exists."""
    try:
        if hasattr(element, 'IsTypedBy') and element.IsTypedBy:
            for rel in element.IsTypedBy:
                if hasattr(rel, 'RelatingType'):
                    type_obj = rel.RelatingType
                    description = type_obj.Description if hasattr(type_obj, 'Description') and type_obj.Description else None
                    return description
    except Exception:
        pass
    return None


def check_for_gkb_keywords(text):
    """
    Check if a text contains keywords related to GKB/plasterboard/drywall.
    Returns True if GKB-related keywords are found.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in GKB_KEYWORDS)


def get_wall_from_door(door):
    """
    Find the wall that contains a door by traversing the relationship:
    Door -> FillsVoids -> IfcOpeningElement -> VoidsElements -> Wall
    
    Returns tuple: (wall_element, opening_element) or (None, None)
    """
    try:
        # Check if door fills any voids
        if hasattr(door, 'FillsVoids') and door.FillsVoids:
            for rel in door.FillsVoids:
                if hasattr(rel, 'RelatingOpeningElement'):
                    opening = rel.RelatingOpeningElement
                    # Check if opening voids any element
                    if hasattr(opening, 'VoidsElements') and opening.VoidsElements:
                        for void_rel in opening.VoidsElements:
                            if hasattr(void_rel, 'RelatingBuildingElement'):
                                wall = void_rel.RelatingBuildingElement
                                return (wall, opening)
    except Exception:
        pass
    
    return (None, None)


def _check_keywords_in_texts(texts, keywords):
    """
    Helper function to check if any keyword is found in any of the provided texts.
    """
    for text in texts:
        if text:
            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords):
                return True
    return False


def get_wall_type_classification(wall):
    """
    Classify the wall type based on its name, type name, and description.
    
    Returns:
        - WALL_TYPE_GKB if it's a plasterboard/drywall
        - WALL_TYPE_CONCRETE if it's concrete
        - WALL_TYPE_BRICK if it's brick/masonry
        - WALL_TYPE_WOOD if it's wood
        - WALL_TYPE_UNKNOWN if classification cannot be determined
    """
    wall_name = get_element_name(wall)
    type_name = get_element_type_name(wall)
    type_description = get_element_type_description(wall)
    texts = [wall_name, type_name, type_description]
    
    # Check for GKB keywords
    if _check_keywords_in_texts(texts, GKB_KEYWORDS):
        return WALL_TYPE_GKB
    
    # Check for concrete
    if _check_keywords_in_texts(texts, CONCRETE_KEYWORDS):
        return WALL_TYPE_CONCRETE
    
    # Check for brick/masonry
    if _check_keywords_in_texts(texts, BRICK_KEYWORDS):
        return WALL_TYPE_BRICK
    
    # Check for wood
    if _check_keywords_in_texts(texts, WOOD_KEYWORDS):
        return WALL_TYPE_WOOD
    
    return WALL_TYPE_UNKNOWN


def get_wall_description_for_output(wall):
    """
    Get a descriptive string for the wall including its IFC type and identifying info.
    """
    wall_name = get_element_name(wall)
    type_name = get_element_type_name(wall)
    ifc_type = wall.is_a()
    
    parts = [ifc_type]
    if type_name:
        parts.append(type_name)
    if wall_name != f"Element #{wall.id()}":
        parts.append(wall_name)
    
    return " / ".join(parts)


def analyze_doors(ifc_file):
    """
    Analyze all doors in the IFC file and group them by wall type.
    
    Returns:
        tuple: (doors_by_wall_type, doors_without_walls)
            - doors_by_wall_type: dict mapping wall types to lists of door info dicts
            - doors_without_walls: list of door info dicts for doors with no wall association
    """
    print("\n" + "="*70)
    print("SEARCHING FOR DOORS (IfcDoor)")
    print("="*70)
    
    doors = ifc_file.by_type('IfcDoor')
    
    if not doors:
        print("\nNo IfcDoor objects found in this file.")
        return {}, []
    
    print(f"\nFound {len(doors)} IfcDoor objects in total.")
    print("\nAnalyzing each door and its surrounding wall...\n")
    
    # Group doors by wall type
    doors_by_wall_type = defaultdict(list)
    doors_without_walls = []
    
    for idx, door in enumerate(doors, 1):
        door_name = get_element_name(door)
        door_type_name = get_element_type_name(door)
        
        print(f"--- Door #{idx} ---")
        print(f"  ID: {door.id()}")
        print(f"  Name: {door_name}")
        if door_type_name:
            print(f"  Type Name: {door_type_name}")
        
        # Find the surrounding wall
        wall, opening = get_wall_from_door(door)
        
        if wall:
            wall_classification = get_wall_type_classification(wall)
            wall_description = get_wall_description_for_output(wall)
            
            print(f"  Surrounding Wall: {wall_description}")
            print(f"  Wall Classification: {wall_classification}")
            
            # Determine how this was detected
            detected_by = []
            if wall_classification == WALL_TYPE_GKB:
                if check_for_gkb_keywords(get_element_name(wall)):
                    detected_by.append("Wall Name")
                if check_for_gkb_keywords(get_element_type_name(wall)):
                    detected_by.append("Wall Type Name")
                if check_for_gkb_keywords(get_element_type_description(wall)):
                    detected_by.append("Wall Type Description")
            
            if wall_classification == WALL_TYPE_GKB:
                print(f"  ✓ GKB Wall detected!")
                if detected_by:
                    print(f"  Detection method: {', '.join(detected_by)}")
            
            doors_by_wall_type[wall_classification].append({
                'door': door,
                'door_id': door.id(),
                'door_name': door_name,
                'door_type_name': door_type_name,
                'wall': wall,
                'wall_classification': wall_classification,
                'wall_description': wall_description,
                'detected_by': ', '.join(detected_by) if detected_by else 'Classification logic'
            })
        else:
            print(f"  Surrounding Wall: Not found")
            print(f"  ⚠ Door is not associated with a wall")
            doors_without_walls.append({
                'door': door,
                'door_id': door.id(),
                'door_name': door_name,
                'door_type_name': door_type_name
            })
        
        print()
    
    return doors_by_wall_type, doors_without_walls


def print_summary(doors_by_wall_type, doors_without_walls):
    """Print a summary of doors grouped by wall type."""
    print("\n" + "="*70)
    print("SUMMARY: DOORS GROUPED BY WALL TYPE")
    print("="*70)
    
    total_doors = sum(len(doors) for doors in doors_by_wall_type.values()) + len(doors_without_walls)
    
    print(f"\nTotal doors analyzed: {total_doors}")
    print(f"Doors with identified walls: {sum(len(doors) for doors in doors_by_wall_type.values())}")
    print(f"Doors without wall association: {len(doors_without_walls)}")
    
    # Print each wall type group
    for wall_type in sorted(doors_by_wall_type.keys()):
        doors = doors_by_wall_type[wall_type]
        print(f"\n{'='*70}")
        print(f"{wall_type} WALLS - {len(doors)} door(s)")
        print("="*70)
        
        if wall_type == WALL_TYPE_GKB:
            print("\nThese are doors in plasterboard/drywall (GKB - Gipskarton) walls:\n")
        
        print(f"{'ID':<10} {'Name':<30} {'IFC Type':<15} {'Type Name':<25} {'Detected by'}")
        print("-" * 110)
        
        for door_info in doors:
            door_id = str(door_info['door_id'])
            door_name = door_info['door_name'][:28]
            ifc_type = door_info['door'].is_a()
            type_name = (door_info['door_type_name'] or 'N/A')[:23]
            detected_by = door_info['detected_by'][:30]
            
            print(f"{door_id:<10} {door_name:<30} {ifc_type:<15} {type_name:<25} {detected_by}")
        
        print()
    
    # Print doors without walls if any
    if doors_without_walls:
        print(f"\n{'='*70}")
        print(f"DOORS WITHOUT WALL ASSOCIATION - {len(doors_without_walls)} door(s)")
        print("="*70)
        print("\nThese doors could not be associated with a surrounding wall:\n")
        
        print(f"{'ID':<10} {'Name':<30} {'IFC Type':<15} {'Type Name'}")
        print("-" * 80)
        
        for door_info in doors_without_walls:
            door_id = str(door_info['door_id'])
            door_name = door_info['door_name'][:28]
            ifc_type = door_info['door'].is_a()
            type_name = (door_info['door_type_name'] or 'N/A')[:23]
            
            print(f"{door_id:<10} {door_name:<30} {ifc_type:<15} {type_name}")
        
        print()
    
    return len(doors_by_wall_type.get(WALL_TYPE_GKB, []))


def analyze_ifc_file(file_path):
    """
    Main analysis function for detecting doors and grouping them by wall type.
    """
    print("\n" + "="*70)
    print("DOOR-WALL TYPE ANALYSIS")
    print("="*70)
    print(f"\nAnalyzing file: {file_path}\n")
    
    try:
        # Open the IFC file
        ifc_file = ifcopenshell.open(file_path)
        print(f"✓ Successfully opened IFC file")
        print(f"  IFC Schema: {ifc_file.schema}")
        
        # Get project information
        projects = ifc_file.by_type("IfcProject")
        if projects:
            project = projects[0]
            project_name = project.Name if hasattr(project, 'Name') and project.Name else 'N/A'
            print(f"  Project Name: {project_name}")
        
        print("\n" + "-"*70)
        print("ANALYSIS STRATEGY:")
        print("-"*70)
        print("1. Search for all IfcDoor objects")
        print("2. Find surrounding wall for each door")
        print("3. Classify wall type (GKB, Concrete, Brick, etc.)")
        print("4. Group doors by wall type")
        print("5. Special focus on GKB (plasterboard/drywall) walls")
        print("-"*70)
        
        # Analyze doors
        doors_by_wall_type, doors_without_walls = analyze_doors(ifc_file)
        
        # Print summary
        gkb_door_count = print_summary(doors_by_wall_type, doors_without_walls)
        
        # Additional notes
        print("\n" + "="*70)
        print("NOTES")
        print("="*70)
        print("\nThis program analyzes:")
        print("  • All doors in the IFC file")
        print("  • Their relationship to surrounding walls")
        print("  • Wall type classification based on names and descriptions")
        print("  • Special detection for GKB (plasterboard/drywall) walls")
        print("\nGKB Detection Keywords:")
        print("  German: GKB, Gipskarton, Gipswand, Trockenbau")
        print("  English: drywall, plasterboard, gypsum board")
        print("\nRelationship chain:")
        print("  IfcDoor → FillsVoids → IfcOpeningElement → VoidsElements → IfcWall")
        
        return gkb_door_count
        
    except Exception as e:
        print(f"\n✗ Error analyzing IFC file: {e}")
        traceback.print_exc()
        return None


def main():
    """Main entry point for the program."""
    print("\n" + "="*70)
    print("DOOR-WALL TYPE ANALYSIS PROGRAM")
    print("Analyzing doors grouped by surrounding wall types")
    print("="*70)
    
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return 0
    
    # Determine which IFC file to analyze
    ifc_file_path = None
    
    if len(sys.argv) > 1:
        # File path provided as argument
        ifc_file_path = sys.argv[1]
        if not os.path.exists(ifc_file_path):
            print(f"\nError: File not found: {ifc_file_path}")
            print("\nUsage:")
            print("  python door_test.py [path_to_ifc_file]")
            print("  python door_test.py --help")
            return 1
    else:
        # Search for IFC files in current directory
        print("\nNo file specified. Searching for IFC files in current directory...")
        ifc_files = find_ifc_files()
        
        if not ifc_files:
            print("\nNo IFC files found in the current directory.")
            print("\nUsage:")
            print("  python door_test.py [path_to_ifc_file]")
            print("\nOr place an IFC file in the current directory.")
            return 1
        
        if len(ifc_files) == 1:
            ifc_file_path = ifc_files[0]
            print(f"\nFound 1 IFC file: {ifc_file_path}")
        else:
            print(f"\nFound {len(ifc_files)} IFC files:")
            for i, file in enumerate(ifc_files, 1):
                print(f"  {i}. {file}")
            
            # Use the first file
            ifc_file_path = ifc_files[0]
            print(f"\nUsing the first file: {ifc_file_path}")
    
    # Analyze the IFC file
    result = analyze_ifc_file(ifc_file_path)
    
    if result is not None:
        print("\n" + "="*70)
        print(f"Analysis complete! Found {result} door(s) in GKB walls.")
        print("="*70 + "\n")
        return 0
    else:
        print("\nAnalysis failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
