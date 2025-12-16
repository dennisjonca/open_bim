#!/usr/bin/env python3
"""
IFC Query Engine
This module provides query functions for extracting specific information from IFC files.
Based on analyze_ifc.py but refactored for web service usage.
"""

import ifcopenshell
from collections import defaultdict


def _get_storey_name(storey):
    """Get a displayable name for a storey."""
    return storey.Name or storey.LongName or f"Storey #{storey.id()}"


def _find_storey_from_space(space):
    """Find the parent storey of a space by traversing spatial relationships."""
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
    """Get the building storey (floor) that contains a product."""
    try:
        # Method 1: Try to get the container through IfcRelContainedInSpatialStructure
        if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
            for rel in product.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    if structure.is_a("IfcBuildingStorey"):
                        return _get_storey_name(structure)
                    elif structure.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(structure)
                        if storey_name:
                            return storey_name
        
        # Method 2: Check through IfcRelReferencedInSpatialStructure
        if hasattr(product, 'ReferencedInStructures') and product.ReferencedInStructures:
            for rel in product.ReferencedInStructures:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    if structure.is_a("IfcBuildingStorey"):
                        return _get_storey_name(structure)
                    elif structure.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(structure)
                        if storey_name:
                            return storey_name
        
        # Method 3: Check through spatial decomposition
        if hasattr(product, 'Decomposes') and product.Decomposes:
            for rel in product.Decomposes:
                if hasattr(rel, 'RelatingObject'):
                    parent = rel.RelatingObject
                    if parent.is_a("IfcBuildingStorey"):
                        return _get_storey_name(parent)
                    elif parent.is_a("IfcSpace"):
                        storey_name = _find_storey_from_space(parent)
                        if storey_name:
                            return storey_name
    except Exception:
        pass
    
    return "Unassigned"


def get_product_space(product):
    """Get the space that contains a product."""
    try:
        # Check containment relationships
        if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
            for rel in product.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    if structure.is_a("IfcSpace"):
                        return structure
        
        # Check referenced relationships
        if hasattr(product, 'ReferencedInStructures') and product.ReferencedInStructures:
            for rel in product.ReferencedInStructures:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    if structure.is_a("IfcSpace"):
                        return structure
    except Exception:
        pass
    
    return None


def get_element_length(element):
    """Get the length of a linear element."""
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
                            if prop.Name in ['Length', 'NominalLength', 'TotalLength']:
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    return float(prop.NominalValue.wrappedValue)
        
        # Note: Geometry-based calculation would require ifcopenshell.geom which is expensive
        # For most IFC files, length should be available in quantities or properties
    except Exception:
        pass
    
    return 0.0


def get_element_area(element):
    """Get the area of an element."""
    try:
        # Try to get from element quantities (IfcElementQuantity) - most common for area data
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_definition = definition.RelatingPropertyDefinition
                    
                    # Check IfcElementQuantity (standard way to store quantities)
                    if property_definition.is_a('IfcElementQuantity'):
                        for quantity in property_definition.Quantities:
                            if quantity.is_a('IfcQuantityArea'):
                                # Common area quantity names
                                if quantity.Name in ['Area', 'NetArea', 'GrossArea', 'TotalArea', 'NetSideArea']:
                                    if hasattr(quantity, 'AreaValue') and quantity.AreaValue:
                                        return float(quantity.AreaValue)
                    
                    # Also check IfcPropertySet (alternative location for area data)
                    elif property_definition.is_a('IfcPropertySet'):
                        for prop in property_definition.HasProperties:
                            if prop.Name in ['Area', 'NetArea', 'GrossArea']:
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    return float(prop.NominalValue.wrappedValue)
    except Exception:
        pass
    
    return 0.0


# ==================== CATEGORY 1: Quantity & Cost Estimation ====================

def count_by_type_and_storey(ifc_file, element_type):
    """Count elements of a specific type per storey."""
    counts = defaultdict(int)
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        storey = get_product_storey(element)
        counts[storey] += 1
    
    return dict(counts)


def count_by_type_total(ifc_file, element_type):
    """Count total elements of a specific type in the building."""
    return len(ifc_file.by_type(element_type))


# ==================== CATEGORY 2: Lengths & Volumes ====================

def get_total_length_by_type(ifc_file, element_type):
    """Get total length of linear elements of a specific type."""
    elements = ifc_file.by_type(element_type)
    total_length = 0.0
    
    for element in elements:
        length = get_element_length(element)
        total_length += length
    
    return total_length


def get_length_by_storey(ifc_file, element_type):
    """Get total length of linear elements per storey."""
    lengths = defaultdict(float)
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        storey = get_product_storey(element)
        length = get_element_length(element)
        lengths[storey] += length
    
    return dict(lengths)


def get_length_by_system(ifc_file, element_type):
    """Get total length of linear elements per MEP system."""
    system_lengths = defaultdict(float)
    
    # Get all systems
    all_systems = ifc_file.by_type("IfcSystem")
    
    for system in all_systems:
        system_name = system.Name or system.LongName or f"System #{system.id()}"
        
        if hasattr(system, 'IsGroupedBy') and system.IsGroupedBy:
            for rel in system.IsGroupedBy:
                if hasattr(rel, 'RelatedObjects'):
                    for obj in rel.RelatedObjects:
                        if obj.is_a(element_type):
                            length = get_element_length(obj)
                            system_lengths[system_name] += length
    
    return dict(system_lengths)


def get_total_area_by_type(ifc_file, element_type):
    """Get total area of elements of a specific type."""
    elements = ifc_file.by_type(element_type)
    total_area = 0.0
    
    for element in elements:
        area = get_element_area(element)
        total_area += area
    
    return total_area


# ==================== CATEGORY 3: Element-Context Questions ====================

def count_elements_by_host_type(ifc_file, element_type, host_type):
    """Count elements installed in a specific host type (e.g., doors in drywall)."""
    count = 0
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        # Check if element fills opening in host
        if hasattr(element, 'FillsVoids') and element.FillsVoids:
            for rel in element.FillsVoids:
                if hasattr(rel, 'RelatingOpeningElement'):
                    opening = rel.RelatingOpeningElement
                    # Check if opening is in the specified host type
                    if hasattr(opening, 'VoidsElements') and opening.VoidsElements:
                        for void_rel in opening.VoidsElements:
                            if hasattr(void_rel, 'RelatingBuildingElement'):
                                host = void_rel.RelatingBuildingElement
                                if host.is_a(host_type):
                                    count += 1
    
    return count


def count_elements_in_space_type(ifc_file, element_type, space_type_name):
    """Count elements in spaces of a specific type (e.g., outlets in offices)."""
    count = 0
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        space = get_product_space(element)
        if space:
            # Check space type/name
            space_name = space.Name or space.LongName or ""
            if space_type_name.lower() in space_name.lower():
                count += 1
    
    return count


def count_elements_per_space(ifc_file, element_type):
    """Count elements per individual space."""
    counts = defaultdict(int)
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        space = get_product_space(element)
        if space:
            space_name = space.Name or space.LongName or f"Space #{space.id()}"
            counts[space_name] += 1
    
    return dict(counts)


# ==================== CATEGORY 4: System-based Questions ====================

def get_elements_by_system(ifc_file, system_name=None):
    """Get elements organized by system (electrical circuits, HVAC, etc.)."""
    system_elements = defaultdict(lambda: defaultdict(int))
    
    all_systems = ifc_file.by_type("IfcSystem")
    
    for system in all_systems:
        sys_name = system.Name or system.LongName or f"System #{system.id()}"
        
        # Filter by system name if provided
        if system_name and system_name.lower() not in sys_name.lower():
            continue
        
        if hasattr(system, 'IsGroupedBy') and system.IsGroupedBy:
            for rel in system.IsGroupedBy:
                if hasattr(rel, 'RelatedObjects'):
                    for obj in rel.RelatedObjects:
                        if obj.is_a("IfcProduct"):
                            product_type = obj.is_a()
                            system_elements[sys_name][product_type] += 1
    
    return dict(system_elements)


def count_elements_per_circuit(ifc_file, element_type):
    """Count elements per electrical circuit."""
    circuit_counts = defaultdict(int)
    
    circuits = ifc_file.by_type("IfcElectricalCircuit")
    
    for circuit in circuits:
        circuit_name = circuit.Name or circuit.LongName or f"Circuit #{circuit.id()}"
        
        if hasattr(circuit, 'IsGroupedBy') and circuit.IsGroupedBy:
            for rel in circuit.IsGroupedBy:
                if hasattr(rel, 'RelatedObjects'):
                    for obj in rel.RelatedObjects:
                        if obj.is_a(element_type):
                            circuit_counts[circuit_name] += 1
    
    return dict(circuit_counts)


# ==================== CATEGORY 5: Space & Usage Analysis ====================

def count_rooms(ifc_file):
    """Count total number of rooms/spaces."""
    return len(ifc_file.by_type("IfcSpace"))


def get_net_area_per_storey(ifc_file):
    """Get total net area per storey."""
    area_by_storey = defaultdict(float)
    
    spaces = ifc_file.by_type("IfcSpace")
    for space in spaces:
        storey = get_product_storey(space)
        area = get_element_area(space)
        area_by_storey[storey] += area
    
    return dict(area_by_storey)


def get_area_by_space_type(ifc_file, space_type_name):
    """Get total area of spaces of a specific type."""
    total_area = 0.0
    spaces = ifc_file.by_type("IfcSpace")
    
    for space in spaces:
        space_name = space.Name or space.LongName or ""
        if space_type_name.lower() in space_name.lower():
            area = get_element_area(space)
            total_area += area
    
    return total_area


def count_elements_per_area(ifc_file, element_type, space_type_name):
    """Count elements per square meter in specific space types."""
    element_count = count_elements_in_space_type(ifc_file, element_type, space_type_name)
    total_area = get_area_by_space_type(ifc_file, space_type_name)
    
    if total_area > 0:
        return element_count / total_area
    return 0.0


# ==================== CATEGORY 6: Compliance & Checking ====================

def check_elements_in_all_spaces(ifc_file, element_type, space_type_name):
    """Check if elements exist in all spaces of a specific type."""
    spaces = ifc_file.by_type("IfcSpace")
    spaces_with_elements = set()
    all_target_spaces = set()
    
    for space in spaces:
        space_name = space.Name or space.LongName or ""
        if space_type_name.lower() in space_name.lower():
            space_id = space.id()
            all_target_spaces.add(space_id)
    
    elements = ifc_file.by_type(element_type)
    for element in elements:
        space = get_product_space(element)
        if space:
            space_name = space.Name or space.LongName or ""
            if space_type_name.lower() in space_name.lower():
                spaces_with_elements.add(space.id())
    
    missing_spaces = all_target_spaces - spaces_with_elements
    return {
        'all_have': len(missing_spaces) == 0,
        'total_spaces': len(all_target_spaces),
        'spaces_with_elements': len(spaces_with_elements),
        'missing_count': len(missing_spaces)
    }


# ==================== CATEGORY 7: Installation & Execution Planning ====================

def count_elements_per_floor(ifc_file):
    """Count all elements per floor."""
    floor_counts = defaultdict(int)
    
    all_products = ifc_file.by_type("IfcProduct")
    for product in all_products:
        storey = get_product_storey(product)
        floor_counts[storey] += 1
    
    return dict(floor_counts)


def get_floor_with_highest_density(ifc_file, element_type=None):
    """Find which floor has the highest installation density."""
    if element_type:
        counts = count_by_type_and_storey(ifc_file, element_type)
    else:
        counts = count_elements_per_floor(ifc_file)
    
    if not counts:
        return None, 0
    
    max_floor = max(counts.items(), key=lambda x: x[1])
    return max_floor


def get_rooms_with_most_devices(ifc_file, element_types):
    """Find rooms with the most devices of specified types."""
    room_counts = defaultdict(int)
    
    for element_type in element_types:
        elements = ifc_file.by_type(element_type)
        for element in elements:
            space = get_product_space(element)
            if space:
                space_name = space.Name or space.LongName or f"Space #{space.id()}"
                room_counts[space_name] += 1
    
    # Sort by count descending
    sorted_rooms = sorted(room_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_rooms


# ==================== CATEGORY 8: Maintenance & Handover ====================

def count_maintainable_devices(ifc_file):
    """Count all maintainable devices in the building."""
    maintainable_types = [
        "IfcElectricDistributionBoard",
        "IfcValve",
        "IfcPump",
        "IfcFan",
        "IfcBoiler",
        "IfcChiller",
        "IfcFilter",
        "IfcSensor",
        "IfcActuator",
        "IfcAlarm"
    ]
    
    total = 0
    for element_type in maintainable_types:
        total += count_by_type_total(ifc_file, element_type)
    
    return total


def locate_distribution_boards(ifc_file):
    """Find locations of all electrical distribution boards."""
    boards = ifc_file.by_type("IfcElectricDistributionBoard")
    locations = []
    
    for board in boards:
        storey = get_product_storey(board)
        space = get_product_space(board)
        space_name = space.Name if space else "Unknown"
        board_name = board.Name or f"Board #{board.id()}"
        
        locations.append({
            'name': board_name,
            'storey': storey,
            'space': space_name
        })
    
    return locations


# ==================== CATEGORY 9: High-value Compound Questions ====================

def count_elements_filtered(ifc_file, element_type, storey_filter=None, space_type_filter=None):
    """Count elements with multiple filters (e.g., outlets in offices on first floor)."""
    count = 0
    elements = ifc_file.by_type(element_type)
    
    for element in elements:
        # Check storey filter
        if storey_filter:
            storey = get_product_storey(element)
            if storey_filter.lower() not in storey.lower():
                continue
        
        # Check space type filter
        if space_type_filter:
            space = get_product_space(element)
            if not space:
                continue
            space_name = space.Name or space.LongName or ""
            if space_type_filter.lower() not in space_name.lower():
                continue
        
        count += 1
    
    return count


# ==================== Helper Functions ====================

def get_all_storeys(ifc_file):
    """Get all building storeys in the IFC file."""
    storeys = []
    for storey in ifc_file.by_type("IfcBuildingStorey"):
        storey_name = _get_storey_name(storey)
        elevation = storey.Elevation if hasattr(storey, 'Elevation') and storey.Elevation is not None else None
        storeys.append((storey_name, elevation))
    
    storeys.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))
    return storeys


def get_available_element_types(ifc_file):
    """Get all unique element types in the IFC file."""
    element_types = set()
    all_products = ifc_file.by_type("IfcProduct")
    
    for product in all_products:
        element_types.add(product.is_a())
    
    return sorted(list(element_types))
