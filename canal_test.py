#!/usr/bin/env python3
"""
Parapet Channel (Brüstungskanal) Test Program
==============================================

This script tests the ifcopenshell API by searching for parapet channels
(cable carrier segments at parapet height) in an IFC file.

A parapet channel (German: "Brüstungskanal") is a cable carrier segment or
cable channel that is typically installed at parapet height (around 0.8-1.3m
from the floor).

Usage:
    python canal_test.py [path_to_ifc_file]
    
If no file is specified, it will search for IFC files in the current directory.
"""

import os
import sys
import glob
import traceback

try:
    import ifcopenshell
except ImportError:
    print("\nError: ifcopenshell is not installed.")
    print("Please install it using: pip install ifcopenshell")
    print("Or install all requirements: pip install -r requirements.txt\n")
    sys.exit(1)


# Typical parapet height range in meters (from floor level)
PARAPET_HEIGHT_MIN = 0.8  # meters
PARAPET_HEIGHT_MAX = 1.3  # meters


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


def get_element_height_from_properties(element):
    """
    Try to get the installation height of an element from its properties.
    Returns height in meters, or None if not found.
    """
    try:
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_def = definition.RelatingPropertyDefinition
                    
                    # Check IfcPropertySet
                    if prop_def.is_a('IfcPropertySet'):
                        for prop in prop_def.HasProperties:
                            # Look for height-related properties
                            prop_name = prop.Name.lower() if hasattr(prop, 'Name') and prop.Name else ""
                            if any(keyword in prop_name for keyword in ['height', 'höhe', 'elevation', 'level']):
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    try:
                                        height = float(prop.NominalValue.wrappedValue)
                                        return height
                                    except (ValueError, TypeError, AttributeError):
                                        pass
    except Exception:
        pass
    return None


def get_element_length(element):
    """
    Get the length of a linear element.
    Returns length in meters, or None if not found.
    """
    try:
        # Try to get from element quantities (IfcElementQuantity) - most common for length data
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_definition = definition.RelatingPropertyDefinition
                    
                    # Check IfcElementQuantity (standard way to store quantities)
                    if property_definition.is_a('IfcElementQuantity'):
                        for quantity in property_definition.Quantities:
                            if quantity.is_a('IfcQuantityLength'):
                                # Common length quantity names
                                if quantity.Name in ['Length', 'NominalLength', 'TotalLength', 'GrossLength', 'NetLength']:
                                    if hasattr(quantity, 'LengthValue') and quantity.LengthValue:
                                        return float(quantity.LengthValue)
                    
                    # Also check IfcPropertySet (alternative location for length data)
                    elif property_definition.is_a('IfcPropertySet'):
                        for prop in property_definition.HasProperties:
                            if prop.Name in ['Length', 'NominalLength', 'TotalLength', 'Länge']:
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    try:
                                        return float(prop.NominalValue.wrappedValue)
                                    except (ValueError, TypeError, AttributeError):
                                        pass
        
        # Note: Geometry-based calculation would require ifcopenshell.geom which is expensive
        # For most IFC files, length should be available in quantities or properties
    except Exception:
        pass
    
    return None


def check_name_for_parapet_keywords(name):
    """
    Check if a name contains keywords related to parapet channels.
    Returns True if parapet-related keywords are found.
    """
    if not name:
        return False
    
    name_lower = name.lower()
    
    # German keywords
    german_keywords = [
        'brüstungskanal',
        'bruestungskanal',
        'brüstung',
        'parapet',
    ]
    
    # English keywords
    english_keywords = [
        'parapet channel',
        'parapet canal',
        'parapet cable',
    ]
    
    all_keywords = german_keywords + english_keywords
    
    return any(keyword in name_lower for keyword in all_keywords)


def get_element_properties(element):
    """
    Get all properties of an element for detailed inspection.
    Returns a dictionary of property sets and their properties.
    """
    properties = {}
    
    try:
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_def = definition.RelatingPropertyDefinition
                    
                    if prop_def.is_a('IfcPropertySet'):
                        pset_name = prop_def.Name if hasattr(prop_def, 'Name') else "Unknown PropertySet"
                        properties[pset_name] = {}
                        
                        for prop in prop_def.HasProperties:
                            prop_name = prop.Name if hasattr(prop, 'Name') and prop.Name else "Unknown"
                            try:
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    prop_value = prop.NominalValue.wrappedValue
                                else:
                                    prop_value = "N/A"
                            except (AttributeError, TypeError):
                                prop_value = "N/A"
                            
                            properties[pset_name][prop_name] = prop_value
    except Exception as e:
        properties["Error"] = str(e)
    
    return properties


def analyze_cable_carriers(ifc_file):
    """
    Analyze all cable carrier segments in the IFC file to find parapet channels.
    """
    print("\n" + "="*70)
    print("SEARCHING FOR CABLE CARRIER SEGMENTS (IfcCableCarrierSegment)")
    print("="*70)
    
    cable_carriers = ifc_file.by_type('IfcCableCarrierSegment')
    
    if not cable_carriers:
        print("\nNo IfcCableCarrierSegment objects found in this file.")
        return []
    
    print(f"\nFound {len(cable_carriers)} IfcCableCarrierSegment objects in total.")
    print("\nAnalyzing each cable carrier segment...\n")
    
    parapet_candidates = []
    
    for idx, carrier in enumerate(cable_carriers, 1):
        element_name = get_element_name(carrier)
        type_name = get_element_type_name(carrier)
        
        print(f"\n--- Cable Carrier #{idx} ---")
        print(f"  ID: {carrier.id()}")
        print(f"  Name: {element_name}")
        if type_name:
            print(f"  Type Name: {type_name}")
        
        # Check 1: Name-based detection
        is_parapet_by_name = False
        if check_name_for_parapet_keywords(element_name):
            print(f"  ✓ Name contains parapet keywords!")
            is_parapet_by_name = True
        if type_name and check_name_for_parapet_keywords(type_name):
            print(f"  ✓ Type name contains parapet keywords!")
            is_parapet_by_name = True
        
        # Check 2: Height-based detection
        height = get_element_height_from_properties(carrier)
        is_parapet_by_height = False
        if height is not None:
            print(f"  Installation Height: {height:.3f} m")
            if PARAPET_HEIGHT_MIN <= height <= PARAPET_HEIGHT_MAX:
                print(f"  ✓ Height is within parapet range ({PARAPET_HEIGHT_MIN}-{PARAPET_HEIGHT_MAX}m)!")
                is_parapet_by_height = True
        else:
            print(f"  Installation Height: Not found in properties")
        
        # Check 3: Get element length
        length = get_element_length(carrier)
        if length is not None:
            print(f"  Length: {length:.3f} m")
        else:
            print(f"  Length: Not found in properties")
        
        # Check 4: Get all properties for inspection
        properties = get_element_properties(carrier)
        if properties:
            print(f"  Properties:")
            for pset_name, props in properties.items():
                print(f"    {pset_name}:")
                for prop_name, prop_value in props.items():
                    print(f"      - {prop_name}: {prop_value}")
        
        # Determine if this is a parapet channel candidate
        if is_parapet_by_name or is_parapet_by_height:
            print(f"\n  >>> POTENTIAL PARAPET CHANNEL DETECTED! <<<")
            parapet_candidates.append({
                'element': carrier,
                'id': carrier.id(),
                'name': element_name,
                'type_name': type_name,
                'height': height,
                'length': length,
                'detected_by_name': is_parapet_by_name,
                'detected_by_height': is_parapet_by_height
            })
    
    return parapet_candidates


def analyze_cable_segments(ifc_file):
    """
    Also check IfcCableSegment as an alternative to cable carrier segments.
    """
    print("\n" + "="*70)
    print("SEARCHING FOR CABLE SEGMENTS (IfcCableSegment)")
    print("="*70)
    
    cable_segments = ifc_file.by_type('IfcCableSegment')
    
    if not cable_segments:
        print("\nNo IfcCableSegment objects found in this file.")
        return []
    
    print(f"\nFound {len(cable_segments)} IfcCableSegment objects in total.")
    print("Checking for parapet-related cable segments...\n")
    
    parapet_candidates = []
    
    for idx, segment in enumerate(cable_segments, 1):
        element_name = get_element_name(segment)
        type_name = get_element_type_name(segment)
        
        # Quick check for parapet keywords
        if check_name_for_parapet_keywords(element_name) or \
           (type_name and check_name_for_parapet_keywords(type_name)):
            print(f"\n--- Cable Segment #{idx} (PARAPET KEYWORD FOUND) ---")
            print(f"  ID: {segment.id()}")
            print(f"  Name: {element_name}")
            if type_name:
                print(f"  Type Name: {type_name}")
            
            height = get_element_height_from_properties(segment)
            if height is not None:
                print(f"  Height: {height:.3f} m")
            
            # Get element length
            length = get_element_length(segment)
            if length is not None:
                print(f"  Length: {length:.3f} m")
            
            # Check if height is in parapet range
            is_parapet_by_height = False
            if height is not None and PARAPET_HEIGHT_MIN <= height <= PARAPET_HEIGHT_MAX:
                is_parapet_by_height = True
            
            parapet_candidates.append({
                'element': segment,
                'id': segment.id(),
                'name': element_name,
                'type_name': type_name,
                'height': height,
                'length': length,
                'detected_by_name': True,  # Already detected by name if we're here
                'detected_by_height': is_parapet_by_height
            })
    
    if not parapet_candidates:
        print("No parapet-related cable segments found.")
    
    return parapet_candidates


def analyze_generic_elements(ifc_file):
    """
    Search in other generic element types that might contain cable channels.
    """
    print("\n" + "="*70)
    print("SEARCHING IN OTHER ELEMENT TYPES")
    print("="*70)
    
    # Check building element proxies (generic elements)
    print("\nChecking IfcBuildingElementProxy...")
    proxies = ifc_file.by_type('IfcBuildingElementProxy')
    print(f"Found {len(proxies)} IfcBuildingElementProxy objects.")
    
    parapet_found = []
    for proxy in proxies:
        element_name = get_element_name(proxy)
        type_name = get_element_type_name(proxy)
        
        if check_name_for_parapet_keywords(element_name) or \
           (type_name and check_name_for_parapet_keywords(type_name)):
            print(f"  ✓ Found parapet-related proxy: {element_name}")
            parapet_found.append(proxy)
    
    # Check flow segments (generic flow element)
    print("\nChecking IfcFlowSegment...")
    flow_segments = ifc_file.by_type('IfcFlowSegment')
    print(f"Found {len(flow_segments)} IfcFlowSegment objects.")
    
    for flow in flow_segments:
        element_name = get_element_name(flow)
        type_name = get_element_type_name(flow)
        
        if check_name_for_parapet_keywords(element_name) or \
           (type_name and check_name_for_parapet_keywords(type_name)):
            print(f"  ✓ Found parapet-related flow segment: {element_name}")
            parapet_found.append(flow)
    
    return parapet_found


def print_summary(all_candidates):
    """Print a summary of all parapet channel candidates found."""
    print("\n" + "="*70)
    print("SUMMARY: PARAPET CHANNEL DETECTION RESULTS")
    print("="*70)
    
    if not all_candidates:
        print("\nNo parapet channels found in this IFC file.")
        print("\nPossible reasons:")
        print("  1. The file doesn't contain parapet channels")
        print("  2. They are not modeled as IfcCableCarrierSegment")
        print("  3. They don't have 'Brüstungskanal' or 'parapet' in their names")
        print("  4. Height information is not included in the IFC file")
        return 0
    
    # Deduplicate candidates by ID, maintaining insertion order
    unique_candidates = {}
    duplicate_count = 0
    for candidate in all_candidates:
        element_id = candidate['id']
        if element_id not in unique_candidates:
            unique_candidates[element_id] = candidate
        else:
            duplicate_count += 1
    
    total_found = len(all_candidates)
    unique_count = len(unique_candidates)
    
    print(f"\nTotal parapet channel candidates found: {total_found}")
    if duplicate_count > 0:
        print(f"  (Note: {duplicate_count} duplicate(s) removed - same element detected multiple times)")
    print(f"Unique parapet channels: {unique_count}")
    
    # Calculate total length if any lengths are available
    total_length = 0.0
    has_length_data = False
    for candidate in unique_candidates.values():
        if candidate.get('length') is not None:
            total_length += candidate['length']
            has_length_data = True
    
    if has_length_data:
        print(f"Total length of parapet channels: {total_length:.3f} m")
    
    print("\nDetailed list:\n")
    
    # Use .values() to maintain insertion order (Python 3.7+ dicts maintain order)
    for idx, candidate in enumerate(unique_candidates.values(), 1):
        print(f"{idx}. ID: {candidate['id']}")
        print(f"   Name: {candidate['name']}")
        print(f"   IFC Type: {candidate['element'].is_a()}")
        if candidate.get('type_name'):
            print(f"   Type Name: {candidate['type_name']}")
        if candidate.get('height') is not None:
            print(f"   Height: {candidate['height']:.3f} m")
        if candidate.get('length') is not None:
            print(f"   Length: {candidate['length']:.3f} m")
        else:
            print(f"   Length: Not available in properties")
        
        detection_methods = []
        if candidate.get('detected_by_name'):
            detection_methods.append("Name keywords")
        if candidate.get('detected_by_height'):
            detection_methods.append("Height range")
        if detection_methods:
            print(f"   Detected by: {', '.join(detection_methods)}")
        print()
    
    return unique_count


def analyze_ifc_file(file_path):
    """
    Main analysis function for detecting parapet channels in an IFC file.
    """
    print("\n" + "="*70)
    print("PARAPET CHANNEL (BRÜSTUNGSKANAL) ANALYSIS")
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
        print("1. Search IfcCableCarrierSegment objects")
        print("2. Check names for 'Brüstungskanal' or 'parapet' keywords")
        print("3. Check height properties (parapet range: 0.8-1.3m)")
        print("4. Also check IfcCableSegment and generic elements")
        print("-"*70)
        
        # Collect all candidates
        all_candidates = []
        
        # Strategy 1: Analyze cable carrier segments
        cable_carrier_candidates = analyze_cable_carriers(ifc_file)
        all_candidates.extend(cable_carrier_candidates)
        
        # Strategy 2: Analyze cable segments
        cable_segment_candidates = analyze_cable_segments(ifc_file)
        all_candidates.extend(cable_segment_candidates)
        
        # Strategy 3: Check other element types
        other_candidates = analyze_generic_elements(ifc_file)
        # Note: other_candidates are just elements, not dictionaries
        # Add them as simple entries
        for elem in other_candidates:
            length = get_element_length(elem)
            all_candidates.append({
                'element': elem,
                'id': elem.id(),
                'name': get_element_name(elem),
                'type_name': get_element_type_name(elem),
                'height': None,
                'length': length,
                'detected_by_name': True,  # Detected by name if in this list
                'detected_by_height': False
            })
        
        # Print summary (returns unique count)
        unique_count = print_summary(all_candidates)
        
        # Additional API testing information
        print("\n" + "="*70)
        print("API TESTING NOTES")
        print("="*70)
        print("\nThis program tests the following ifcopenshell API features:")
        print("  • ifc_file.by_type() - Getting elements by IFC type")
        print("  • element.Name, element.LongName - Basic element attributes")
        print("  • element.IsTypedBy - Getting element type information")
        print("  • element.IsDefinedBy - Getting property sets")
        print("  • IfcPropertySet - Reading custom properties")
        print("  • Property traversal - Searching for height/elevation data")
        print("\nLimitations discovered:")
        print("  • Height information may not be in properties")
        print("  • Element naming varies by BIM software")
        print("  • Spatial relationships don't always include height offset")
        print("  • Some elements may use generic types (IfcBuildingElementProxy)")
        print("\nNote about IFC Element IDs:")
        print("  • Each IFC element has a unique ID within the file")
        print("  • The same element cannot have multiple IDs")
        print("  • If duplicates are found, they were detected by multiple strategies")
        print("  • The summary automatically removes duplicates based on ID")
        
        return unique_count
        
    except Exception as e:
        print(f"\n✗ Error analyzing IFC file: {e}")
        traceback.print_exc()
        return None


def main():
    """Main entry point for the program."""
    print("\n" + "="*70)
    print("PARAPET CHANNEL TEST PROGRAM")
    print("Testing ifcopenshell API with cable carrier segment detection")
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
            print("  python canal_test.py [path_to_ifc_file]")
            print("  python canal_test.py --help")
            return 1
    else:
        # Search for IFC files in current directory
        print("\nNo file specified. Searching for IFC files in current directory...")
        ifc_files = find_ifc_files()
        
        if not ifc_files:
            print("\nNo IFC files found in the current directory.")
            print("\nUsage:")
            print("  python canal_test.py [path_to_ifc_file]")
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
        print(f"Analysis complete! Found {result} parapet channel candidate(s).")
        print("="*70 + "\n")
        return 0
    else:
        print("\nAnalysis failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
