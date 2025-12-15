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


# Common BIM object types to count (for quick summary section)
# Note: Some types also appear in PRODUCT_CATEGORIES below for comprehensive listing
# Common BIM object types to count
OBJECT_TYPES = [
    "IfcWall",
    # Vertical building element used to divide or enclose spaces (structural or non-structural)
    "IfcWallStandardCase",
    # Simplified wall with standard geometry (extruded profile); preferred for analysis and exchange
    "IfcDoor",
    # Opening element that allows access through a wall or partition
    "IfcWindow",
    # Opening element that provides light and/or ventilation through a wall or roof
    "IfcSlab",
    # Horizontal (or near-horizontal) element such as floors, ceilings, or flat roofs
    "IfcBeam",
    # Horizontal or inclined structural element that carries loads
    "IfcColumn",
    # Vertical structural element that transfers loads to foundations
    "IfcStair",
    # Element providing vertical circulation between building levels
    "IfcRoof",
    # Building element that covers the top of a structure
    "IfcSpace",
    # Volumetric area representing a room or usable space (air volume, not a physical element)
    "IfcFurnishingElement",
    # Movable or fixed furniture such as desks, cabinets, or seating
    "IfcBuildingElementProxy",
    # Generic fallback element used when no specific IFC class is defined or mapped
]

# Product type categories for better organization
PRODUCT_CATEGORIES = {
    "Structural Elements": [
        "IfcWall", "IfcWallStandardCase", "IfcBeam", "IfcColumn", "IfcSlab",
        "IfcFooting", "IfcPile", "IfcRailing", "IfcRamp", "IfcRampFlight",
        "IfcRoof", "IfcStair", "IfcStairFlight", "IfcPlate", "IfcMember",
        "IfcCovering", "IfcCurtainWall"
    ],
    "Openings": [
        "IfcDoor", "IfcWindow", "IfcOpeningElement"
    ],
    "MEP & HVAC": [
        "IfcAirTerminal", "IfcAirTerminalBox", "IfcDamper", "IfcDuctFitting",
        "IfcDuctSegment", "IfcDuctSilencer", "IfcFan", "IfcFilter",
        "IfcFlowController", "IfcFlowFitting", "IfcFlowMeter", "IfcFlowMovingDevice",
        "IfcFlowSegment", "IfcFlowStorageDevice", "IfcFlowTerminal",
        "IfcFlowTreatmentDevice", "IfcPipeFitting", "IfcPipeSegment",
        "IfcPump", "IfcTank", "IfcValve", "IfcBoiler", "IfcChiller",
        "IfcCoil", "IfcCondenser", "IfcCooledBeam", "IfcCoolingTower",
        "IfcEvaporativeCooler", "IfcEvaporator", "IfcHeatExchanger",
        "IfcHumidifier", "IfcTubeBundle", "IfcUnitaryEquipment",
        "IfcSpaceHeater", "IfcAirToAirHeatRecovery"
    ],
    "Electrical & Lighting": [
        "IfcLamp", "IfcLightFixture", "IfcElectricAppliance", "IfcElectricDistributionBoard",
        "IfcElectricFlowStorageDevice", "IfcElectricGenerator", "IfcElectricMotor",
        "IfcElectricTimeControl", "IfcCableCarrierFitting", "IfcCableCarrierSegment",
        "IfcCableFitting", "IfcCableSegment", "IfcJunctionBox", "IfcMotorConnection",
        "IfcOutlet", "IfcSwitchingDevice", "IfcTransformer", "IfcProtectiveDevice"
    ],
    "Plumbing & Sanitary": [
        "IfcSanitaryTerminal", "IfcWasteTerminal", "IfcFireSuppressionTerminal",
        "IfcStackTerminal", "IfcInterceptor"
    ],
    "Sensors & Controls": [
        "IfcSensor", "IfcActuator", "IfcAlarm", "IfcController", "IfcUnitaryControlElement",
        "IfcProtectiveDeviceTrippingUnit", "IfcFlowInstrument"
    ],
    "Furnishing & Equipment": [
        "IfcFurniture", "IfcFurnishingElement", "IfcSystemFurnitureElement",
        "IfcMedicalDevice", "IfcAudioVisualAppliance", "IfcCommunicationsAppliance"
    ],
    "Transport": [
        "IfcTransportElement"
    ],
    "Distribution": [
        "IfcDistributionElement", "IfcDistributionControlElement", "IfcDistributionFlowElement",
        "IfcDistributionChamberElement", "IfcEnergyConversionDevice"
    ],
    "Building Services": [
        "IfcBuildingElementProxy", "IfcBuildingElementPart", "IfcDiscreteAccessory",
        "IfcFastener", "IfcMechanicalFastener", "IfcReinforcingBar", "IfcReinforcingMesh",
        "IfcTendon", "IfcTendonAnchor"
    ],
    "Spaces & Zones": [
        "IfcSpace", "IfcZone"
    ],
    "Other Products": []  # Catch-all for uncategorized products
}


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


def _get_storey_name(storey):
    """
    Get a displayable name for a storey.
    
    Args:
        storey: IfcBuildingStorey element
        
    Returns:
        str: Storey name string
    """
    return storey.Name or storey.LongName or f"Storey #{storey.id()}"


def _find_storey_from_space(space):
    """
    Find the parent storey of a space by traversing spatial relationships.
    
    Args:
        space: IfcSpace element
        
    Returns:
        str or None: Storey name string if found, None otherwise
    """
    # Try containment relationships
    if hasattr(space, 'ContainedInStructure') and space.ContainedInStructure:
        for space_rel in space.ContainedInStructure:
            if hasattr(space_rel, 'RelatingStructure'):
                parent = space_rel.RelatingStructure
                if parent.is_a("IfcBuildingStorey"):
                    return _get_storey_name(parent)
    
    # Try spatial decomposition
    if hasattr(space, 'Decomposes') and space.Decomposes:
        for space_rel in space.Decomposes:
            if hasattr(space_rel, 'RelatingObject'):
                parent = space_rel.RelatingObject
                if parent.is_a("IfcBuildingStorey"):
                    return _get_storey_name(parent)
    
    return None


def get_product_storey(product):
    """
    Get the building storey (floor) that contains a product.
    
    Args:
        product: IFC product element
        
    Returns:
        Storey name or 'Unassigned' if not found
    """
    try:
        # Method 1: Try to get the container through IfcRelContainedInSpatialStructure
        if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
            for rel in product.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    # Check if it's directly in a storey
                    if structure.is_a("IfcBuildingStorey"):
                        return _get_storey_name(structure)
                    # Check if it's in a space - traverse up to find the storey
                    elif structure.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(structure)
                        if storey_name:
                            return storey_name
        
        # Method 2: Check through IfcRelReferencedInSpatialStructure
        # This is often used for distribution elements (MEP, outlets, etc.)
        if hasattr(product, 'ReferencedInStructures') and product.ReferencedInStructures:
            for rel in product.ReferencedInStructures:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    # Check if it's directly referenced in a storey
                    if structure.is_a("IfcBuildingStorey"):
                        return _get_storey_name(structure)
                    # Check if it's referenced in a space
                    elif structure.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(structure)
                        if storey_name:
                            return storey_name
        
        # Method 3: Check through spatial decomposition (IfcRelAggregates)
        # Products may be part of an aggregate where the parent is a storey
        if hasattr(product, 'Decomposes') and product.Decomposes:
            for rel in product.Decomposes:
                if hasattr(rel, 'RelatingObject'):
                    parent = rel.RelatingObject
                    # Direct decomposition by storey
                    if parent.is_a("IfcBuildingStorey"):
                        return _get_storey_name(parent)
                    # Check if decomposed by a space
                    elif parent.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(parent)
                        if storey_name:
                            return storey_name
    except Exception:
        pass
    
    return "Unassigned"


def get_all_storeys(ifc_file):
    """
    Get all building storeys in the IFC file.
    
    Args:
        ifc_file: Opened IFC file object
        
    Returns:
        List of tuples (storey_name, elevation) sorted by elevation
    """
    storeys = []
    for storey in ifc_file.by_type("IfcBuildingStorey"):
        storey_name = _get_storey_name(storey)
        # Get elevation, use None if not available (not 0.0 as that's a valid ground floor elevation)
        elevation = storey.Elevation if hasattr(storey, 'Elevation') and storey.Elevation is not None else None
        storeys.append((storey_name, elevation))
    
    # Sort by elevation (lowest to highest), putting None values at the end
    storeys.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))
    
    return storeys


def get_products_by_storey(ifc_file):
    """
    Organize all products by building storey (floor).
    
    Args:
        ifc_file: Opened IFC file object
        
    Returns:
        Dictionary mapping storey names to product type counts
    """
    storey_products = {}
    all_products = ifc_file.by_type("IfcProduct")
    
    for product in all_products:
        storey_name = get_product_storey(product)
        product_type = product.is_a()
        
        if storey_name not in storey_products:
            storey_products[storey_name] = {}
        
        if product_type not in storey_products[storey_name]:
            storey_products[storey_name][product_type] = 0
        
        storey_products[storey_name][product_type] += 1
    
    return storey_products


def analyze_unassigned_objects(ifc_file, storey_products):
    """
    Analyze unassigned objects to help understand why they lack storey assignment.
    
    Args:
        ifc_file: Opened IFC file object
        storey_products: Dictionary from get_products_by_storey()
    """
    if "Unassigned" not in storey_products:
        return
    
    print(f"\n{'='*60}")
    print("Analyzing Unassigned Objects:")
    print(f"{'='*60}\n")
    
    print("Checking spatial relationships for unassigned objects...")
    print("This can help identify if objects are related to spaces that")
    print("aren't properly linked to storeys.\n")
    
    all_products = ifc_file.by_type("IfcProduct")
    unassigned_with_space = {}
    unassigned_with_no_relationship = {}
    
    for product in all_products:
        storey_name = get_product_storey(product)
        if storey_name != "Unassigned":
            continue
        
        product_type = product.is_a()
        has_spatial_relationship = False
        space_info = []
        
        # Check if contained in any structure
        if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
            has_spatial_relationship = True
            for rel in product.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    space_info.append(f"Contained in {structure.is_a()}")
        
        # Check if referenced in any structure
        if hasattr(product, 'ReferencedInStructures') and product.ReferencedInStructures:
            has_spatial_relationship = True
            for rel in product.ReferencedInStructures:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    space_info.append(f"Referenced in {structure.is_a()}")
        
        # Check if part of any decomposition
        if hasattr(product, 'Decomposes') and product.Decomposes:
            has_spatial_relationship = True
            for rel in product.Decomposes:
                if hasattr(rel, 'RelatingObject'):
                    parent = rel.RelatingObject
                    space_info.append(f"Decomposes {parent.is_a()}")
        
        if has_spatial_relationship:
            key = f"{product_type}"
            if key not in unassigned_with_space:
                unassigned_with_space[key] = {"count": 0, "relationships": set()}
            unassigned_with_space[key]["count"] += 1
            unassigned_with_space[key]["relationships"].update(space_info)
        else:
            if product_type not in unassigned_with_no_relationship:
                unassigned_with_no_relationship[product_type] = 0
            unassigned_with_no_relationship[product_type] += 1
    
    if unassigned_with_space:
        print("Objects with spatial relationships but no storey assignment:")
        print("-" * 60)
        for product_type, info in sorted(unassigned_with_space.items(), 
                                         key=lambda x: x[1]["count"], reverse=True):
            print(f"  {product_type:40s}: {info['count']:5d}")
            for rel in sorted(info["relationships"]):
                print(f"    → {rel}")
        print()
    
    if unassigned_with_no_relationship:
        print("Objects with NO spatial relationships:")
        print("-" * 60)
        for product_type, count in sorted(unassigned_with_no_relationship.items(), 
                                          key=lambda x: x[1], reverse=True):
            print(f"  {product_type:40s}: {count:5d}")
        print()
    
    print("Recommendation:")
    print("  • Objects 'Contained in' or 'Referenced in' IfcSpace should have")
    print("    their spaces properly linked to an IfcBuildingStorey")
    print("  • Objects with no spatial relationships may need to be assigned")
    print("    to a space or storey in your BIM authoring tool")
    print(f"{'='*60}\n")


def display_products_by_storey(ifc_file, storey_products):
    """
    Display products organized by building storey (floor).
    
    Args:
        ifc_file: Opened IFC file object
        storey_products: Dictionary from get_products_by_storey()
    """
    print(f"\n{'='*60}")
    print("Products by Floor/Storey:")
    print(f"{'='*60}\n")
    
    # Get all storeys sorted by elevation
    all_storeys = get_all_storeys(ifc_file)
    storey_names = [name for name, _ in all_storeys]
    
    # Add "Unassigned" at the end if it exists
    if "Unassigned" in storey_products and "Unassigned" not in storey_names:
        storey_names.append("Unassigned")
    
    grand_total = 0
    
    for storey_name in storey_names:
        if storey_name not in storey_products:
            continue
            
        products = storey_products[storey_name]
        storey_total = sum(products.values())
        grand_total += storey_total
        
        # Get elevation info for display
        elevation_info = ""
        for name, elev in all_storeys:
            if name == storey_name:
                if elev is not None:
                    elevation_info = f" (Elevation: {elev:.2f}m)"
                break
        
        print(f"\n{storey_name}{elevation_info} - {storey_total} items:")
        print("-" * 60)
        
        # Sort products by count (highest first)
        sorted_products = sorted(products.items(), key=lambda x: x[1], reverse=True)
        
        for product_type, count in sorted_products:
            print(f"  {product_type:40s}: {count:5d}")
    
    print(f"\n{'='*60}")
    print(f"Total Products Across All Floors: {grand_total}")
    print(f"{'='*60}\n")


def get_all_product_types(ifc_file):
    """
    Get all unique product types in the IFC file.
    
    Args:
        ifc_file: Opened IFC file object
        
    Returns:
        Dictionary mapping product type names to counts
    """
    all_products = ifc_file.by_type("IfcProduct")
    product_counts = {}
    
    for product in all_products:
        product_type = product.is_a()
        product_counts[product_type] = product_counts.get(product_type, 0) + 1
    
    return product_counts


def categorize_products(product_counts):
    """
    Organize product types into meaningful categories.
    
    Args:
        product_counts: Dictionary of product type names to counts
        
    Returns:
        Dictionary mapping category names to lists of (type, count) tuples
    """
    categorized = {category: [] for category in PRODUCT_CATEGORIES.keys()}
    
    # Create a reverse mapping for quick lookup
    type_to_category = {}
    for category, types in PRODUCT_CATEGORIES.items():
        for ptype in types:
            type_to_category[ptype] = category
    
    # Categorize each product type
    for product_type, count in product_counts.items():
        category = type_to_category.get(product_type, "Other Products")
        categorized[category].append((product_type, count))
    
    # Remove empty categories
    categorized = {k: v for k, v in categorized.items() if v}
    
    return categorized


def display_categorized_products(categorized_products):
    """
    Display products organized by category.
    
    Args:
        categorized_products: Dictionary from categorize_products()
    """
    print(f"\n{'='*60}")
    print("All Products by Category:")
    print(f"{'='*60}\n")
    
    total_products = 0
    
    for category in sorted(categorized_products.keys()):
        products = categorized_products[category]
        category_total = sum(count for _, count in products)
        total_products += category_total
        
        print(f"\n{category} ({category_total} items):")
        print("-" * 60)
        
        for product_type, count in sorted(products, key=lambda x: x[1], reverse=True):
            print(f"  {product_type:40s}: {count:5d}")
    
    print(f"\n{'='*60}")
    print(f"Total Products Across All Categories: {total_products}")
    print(f"{'='*60}\n")


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
        
        # Get and display all product types categorized
        product_counts = get_all_product_types(ifc_file)
        categorized = categorize_products(product_counts)
        display_categorized_products(categorized)
        
        # Get and display products organized by floor/storey
        storey_products = get_products_by_storey(ifc_file)
        display_products_by_storey(ifc_file, storey_products)
        
        # Analyze unassigned objects to help users understand why objects lack storey assignment
        analyze_unassigned_objects(ifc_file, storey_products)
        
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
