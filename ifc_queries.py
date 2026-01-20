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
                                if quantity.Name in ['Length', 'NominalLength', 'TotalLength', 'GrossLength',
                                                     'NetLength']:
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
    """Get all building storeys in the IFC file, sorted by elevation from lowest to highest."""
    storeys = []
    for storey in ifc_file.by_type("IfcBuildingStorey"):
        storey_name = _get_storey_name(storey)
        elevation = storey.Elevation if hasattr(storey, 'Elevation') and storey.Elevation is not None else None
        storeys.append((storey_name, elevation))

    # Sort by elevation: None values last, then by elevation (including negative values for basements)
    storeys.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))
    return storeys


def get_available_element_types(ifc_file):
    """Get all unique element types in the IFC file."""
    element_types = set()
    all_products = ifc_file.by_type("IfcProduct")

    for product in all_products:
        element_types.add(product.is_a())

    return sorted(list(element_types))


def sort_storey_data(ifc_file, storey_dict):
    """
    Sort a dictionary with storey names as keys by elevation.
    Returns a list of [storey_name, value] pairs sorted by elevation.
    """
    # Get all storeys with their elevations
    storey_elevations = {}
    for storey in ifc_file.by_type("IfcBuildingStorey"):
        storey_name = _get_storey_name(storey)
        elevation = storey.Elevation if hasattr(storey, 'Elevation') and storey.Elevation is not None else None
        storey_elevations[storey_name] = elevation

    # Sort the dictionary items by elevation
    sorted_items = []
    for storey_name, value in storey_dict.items():
        elevation = storey_elevations.get(storey_name, None)
        sorted_items.append((storey_name, value, elevation))

    # Sort by elevation (None values last, then by elevation ascending)
    sorted_items.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else float('inf')))

    # Return as [storey_name, value] pairs
    return [[item[0], item[1]] for item in sorted_items]


def get_all_objects_by_storey(ifc_file):
    """
    Get a comprehensive list of all IFC objects grouped by storey.

    Args:
        ifc_file: Opened IFC file object

    Returns:
        Dictionary mapping storey names to object type counts
        Format: {storey_name: {object_type: count}}
    """
    storey_objects = defaultdict(lambda: defaultdict(int))

    # Get all products
    all_products = ifc_file.by_type("IfcProduct")

    for product in all_products:
        storey = get_product_storey(product)
        object_type = product.is_a()
        storey_objects[storey][object_type] += 1

    return dict(storey_objects)


# ============================================================================
# Special Query Functions for Door Analysis and Parapet Channels
# ============================================================================

# Wall type constants (matching door_test.py) - German translations for web UI display
# Note: door_test.py (CLI tool) maintains English constants for international use
WALL_TYPE_GKB = 'GKB-Wand'
WALL_TYPE_CONCRETE = 'Betonwand'
WALL_TYPE_BRICK = 'Ziegelwand'
WALL_TYPE_WOOD = 'Holzwand'
WALL_TYPE_UNKNOWN = 'Unbekannt'

# Keyword constants for wall type detection
GKB_KEYWORDS = [
    'gkb', 'gipskarton', 'gipswand', 'trockenbau', 'trockenbauwand',
    'drywall', 'plasterboard', 'gypsum board', 'gypsum wall',
]
CONCRETE_KEYWORDS = ['beton', 'concrete', 'stahlbeton']
BRICK_KEYWORDS = ['ziegel', 'brick', 'mauerwerk', 'masonry', 'stein']
WOOD_KEYWORDS = ['holz', 'wood', 'timber']


def _get_element_type_name(element):
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


def _get_element_type_description(element):
    """Get the description of an element's type if it exists."""
    try:
        if hasattr(element, 'IsTypedBy') and element.IsTypedBy:
            for rel in element.IsTypedBy:
                if hasattr(rel, 'RelatingType'):
                    type_obj = rel.RelatingType
                    description = type_obj.Description if hasattr(type_obj,
                                                                  'Description') and type_obj.Description else None
                    return description
    except Exception:
        pass
    return None


def _get_wall_from_door(door):
    """
    Find the wall that contains a door by traversing the relationship:
    Door -> FillsVoids -> IfcOpeningElement -> VoidsElements -> Wall

    Returns tuple: (wall_element, opening_element) or (None, None)
    """
    try:
        if hasattr(door, 'FillsVoids') and door.FillsVoids:
            for rel in door.FillsVoids:
                if hasattr(rel, 'RelatingOpeningElement'):
                    opening = rel.RelatingOpeningElement
                    if hasattr(opening, 'VoidsElements') and opening.VoidsElements:
                        for void_rel in opening.VoidsElements:
                            if hasattr(void_rel, 'RelatingBuildingElement'):
                                wall = void_rel.RelatingBuildingElement
                                return (wall, opening)
    except Exception:
        pass
    return (None, None)


def _check_keywords_in_texts(texts, keywords):
    """Helper function to check if any keyword is found in any of the provided texts."""
    for text in texts:
        if text:
            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords):
                return True
    return False


def _get_wall_type_classification(wall):
    """
    Classify the wall type based on its name, type name, and description.

    Returns:
        - WALL_TYPE_GKB if it's a plasterboard/drywall
        - WALL_TYPE_CONCRETE if it's concrete
        - WALL_TYPE_BRICK if it's brick/masonry
        - WALL_TYPE_WOOD if it's wood
        - WALL_TYPE_UNKNOWN if classification cannot be determined
    """
    # Get wall name
    wall_name = wall.Name if hasattr(wall, 'Name') and wall.Name else None
    if not wall_name:
        wall_name = wall.LongName if hasattr(wall, 'LongName') and wall.LongName else None

    type_name = _get_element_type_name(wall)
    type_description = _get_element_type_description(wall)
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


def count_doors_by_wall_type(ifc_file):
    """
    Count doors grouped by surrounding wall type (GKB, Concrete, Brick, etc.).
    Based on functionality from door_test.py.

    Returns:
        Dictionary mapping wall types to door counts
        Format: {wall_type: count}
    """
    doors = ifc_file.by_type('IfcDoor')
    wall_type_counts = defaultdict(int)

    for door in doors:
        wall, _ = _get_wall_from_door(door)

        if wall:
            wall_classification = _get_wall_type_classification(wall)
            wall_type_counts[wall_classification] += 1
        else:
            wall_type_counts['Keine Wandzuordnung'] += 1

    return dict(wall_type_counts)


# Parapet channel detection constants (matching canal_test.py)
PARAPET_HEIGHT_MIN = 0.8  # meters
PARAPET_HEIGHT_MAX = 1.3  # meters


def _check_name_for_parapet_keywords(name):
    """
    Check if a name contains keywords related to parapet channels.
    Returns True if parapet-related keywords are found.
    """
    if not name:
        return False

    name_lower = name.lower()

    # German and English keywords
    keywords = [
        'brüstungskanal', 'bruestungskanal', 'brüstung',
        'parapet', 'parapet channel', 'parapet canal', 'parapet cable',
    ]

    return any(keyword in name_lower for keyword in keywords)


def _get_element_height_from_properties(element):
    """
    Try to get the installation height of an element from its properties.
    Returns height in meters, or None if not found.
    """
    try:
        if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
            for definition in element.IsDefinedBy:
                if definition.is_a('IfcRelDefinesByProperties'):
                    prop_def = definition.RelatingPropertyDefinition

                    if prop_def.is_a('IfcPropertySet'):
                        for prop in prop_def.HasProperties:
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


def get_parapet_channels_by_type(ifc_file):
    """
    Find and count parapet channels (Brüstungskanäle) grouped by element type.
    Based on functionality from canal_test.py.

    Returns:
        Dictionary with element types as keys and list of parapet info dicts as values
        Format: {
            element_type: [
                {
                    'id': element_id,
                    'name': element_name,
                    'type_name': type_name,
                    'height': height_in_meters,
                    'length': length_in_meters,
                    'detected_by_name': bool,
                    'detected_by_height': bool
                },
                ...
            ]
        }
    """
    parapet_channels = defaultdict(list)

    # Search in different element types that could be parapet channels
    element_types_to_check = [
        'IfcCableCarrierSegment',
        'IfcCableSegment',
        'IfcBuildingElementProxy',
        'IfcFlowSegment'
    ]

    for elem_type in element_types_to_check:
        elements = ifc_file.by_type(elem_type)

        for element in elements:
            # Get element info
            element_name = element.Name if hasattr(element, 'Name') and element.Name else None
            if not element_name:
                element_name = element.LongName if hasattr(element,
                                                           'LongName') and element.LongName else f"Element #{element.id()}"

            type_name = _get_element_type_name(element)

            # Check 1: Name-based detection
            is_parapet_by_name = False
            if _check_name_for_parapet_keywords(element_name):
                is_parapet_by_name = True
            if type_name and _check_name_for_parapet_keywords(type_name):
                is_parapet_by_name = True

            # Check 2: Height-based detection
            height = _get_element_height_from_properties(element)
            is_parapet_by_height = False
            if height is not None and PARAPET_HEIGHT_MIN <= height <= PARAPET_HEIGHT_MAX:
                is_parapet_by_height = True

            # If detected by name or height, add to results
            if is_parapet_by_name or is_parapet_by_height:
                length = get_element_length(element)

                parapet_info = {
                    'id': element.id(),
                    'name': element_name,
                    'type_name': type_name,
                    'height': height,
                    'length': length,
                    'detected_by_name': is_parapet_by_name,
                    'detected_by_height': is_parapet_by_height
                }

                parapet_channels[elem_type].append(parapet_info)

    return dict(parapet_channels)


def get_parapet_channels_summary(ifc_file):
    """
    Get a summary of parapet channels with total counts and lengths.

    Returns:
        Dictionary with summary information:
        {
            'by_type': {element_type: {'count': int, 'total_length': float}},
            'total_count': int,
            'total_length': float
        }
    """
    parapet_channels = get_parapet_channels_by_type(ifc_file)

    summary = {
        'by_type': {},
        'total_count': 0,
        'total_length': 0.0
    }

    # Track unique IDs to avoid double counting
    seen_ids = set()

    for elem_type, channels in parapet_channels.items():
        type_count = 0
        type_length = 0.0

        for channel in channels:
            channel_id = channel['id']

            # Only count unique elements
            if channel_id not in seen_ids:
                seen_ids.add(channel_id)
                type_count += 1
                summary['total_count'] += 1

                if channel['length'] is not None:
                    type_length += channel['length']
                    summary['total_length'] += channel['length']

        if type_count > 0:
            summary['by_type'][elem_type] = {
                'count': type_count,
                'total_length': type_length
            }

    return summary


def get_cable_carrier_segments_detailed(ifc_file):
    """
    Get detailed information about all CableCarrierSegments, categorized by whether
    they are parapet-related or not.

    Returns:
        Dictionary with detailed categorization:
        {
            'parapet_channels': {
                'count': int,
                'total_length': float,
                'items': [list of parapet channel info dicts]
            },
            'other_cable_carriers': {
                'count': int,
                'total_length': float,
                'items': [list of non-parapet cable carrier info dicts]
            },
            'total_count': int,
            'total_length': float
        }
    """
    result = {
        'parapet_channels': {
            'count': 0,
            'total_length': 0.0,
            'items': []
        },
        'other_cable_carriers': {
            'count': 0,
            'total_length': 0.0,
            'items': []
        },
        'total_count': 0,
        'total_length': 0.0
    }

    # Get all CableCarrierSegments
    cable_carriers = ifc_file.by_type('IfcCableCarrierSegment')

    for element in cable_carriers:
        # Get element info
        element_name = element.Name if hasattr(element, 'Name') and element.Name else None
        if not element_name:
            element_name = element.LongName if hasattr(element,
                                                       'LongName') and element.LongName else f"Element #{element.id()}"

        type_name = _get_element_type_name(element)
        height = _get_element_height_from_properties(element)
        length = get_element_length(element)

        # Check if it's a parapet channel
        is_parapet_by_name = False
        if _check_name_for_parapet_keywords(element_name):
            is_parapet_by_name = True
        if type_name and _check_name_for_parapet_keywords(type_name):
            is_parapet_by_name = True

        is_parapet_by_height = False
        if height is not None and PARAPET_HEIGHT_MIN <= height <= PARAPET_HEIGHT_MAX:
            is_parapet_by_height = True

        info = {
            'id': element.id(),
            'name': element_name,
            'type_name': type_name,
            'height': height,
            'length': length
        }

        # Categorize
        if is_parapet_by_name or is_parapet_by_height:
            result['parapet_channels']['items'].append(info)
            result['parapet_channels']['count'] += 1
            if length is not None:
                result['parapet_channels']['total_length'] += length
        else:
            result['other_cable_carriers']['items'].append(info)
            result['other_cable_carriers']['count'] += 1
            if length is not None:
                result['other_cable_carriers']['total_length'] += length

        # Update totals
        result['total_count'] += 1
        if length is not None:
            result['total_length'] += length

    return result


def _check_name_for_drinkable_water_keywords(name):
    """
    Check if a pipe name contains keywords indicating it's for drinkable water.
    German terms: Edelstahlrohr (stainless steel pipe), Kupferrohr (copper pipe)
    """
    if not name:
        return False
    
    name_lower = name.lower()
    drinkable_keywords = [
        'edelstahl',      # stainless steel
        'kupfer',         # copper
        'trinkwasser',    # drinking water
        'potable',        # potable water (English)
        'drinking',       # drinking water (English)
    ]
    
    return any(keyword in name_lower for keyword in drinkable_keywords)


def get_pipe_segments_detailed(ifc_file):
    """
    Get detailed information about all PipeSegments, categorized by whether
    they are for drinkable water or other purposes (e.g., sewage).

    Returns:
        Dictionary with detailed categorization:
        {
            'drinkable_water_pipes': {
                'count': int,
                'total_length': float,
                'items': [list of drinkable water pipe info dicts]
            },
            'other_pipes': {
                'count': int,
                'total_length': float,
                'items': [list of other pipe info dicts]
            },
            'total_count': int,
            'total_length': float
        }
    """
    result = {
        'drinkable_water_pipes': {
            'count': 0,
            'total_length': 0.0,
            'items': []
        },
        'other_pipes': {
            'count': 0,
            'total_length': 0.0,
            'items': []
        },
        'total_count': 0,
        'total_length': 0.0
    }

    # Get all PipeSegments
    pipe_segments = ifc_file.by_type('IfcPipeSegment')

    for element in pipe_segments:
        # Get element info
        element_name = element.Name if hasattr(element, 'Name') and element.Name else None
        if not element_name:
            if hasattr(element, 'LongName') and element.LongName:
                element_name = element.LongName
            else:
                element_name = f"Element #{element.id()}"

        type_name = _get_element_type_name(element)
        length = get_element_length(element)

        # Check if it's for drinkable water based on name or type
        is_drinkable_water = False
        if _check_name_for_drinkable_water_keywords(element_name):
            is_drinkable_water = True
        if type_name and _check_name_for_drinkable_water_keywords(type_name):
            is_drinkable_water = True

        info = {
            'id': element.id(),
            'name': element_name,
            'type_name': type_name,
            'length': length
        }

        # Categorize
        if is_drinkable_water:
            result['drinkable_water_pipes']['items'].append(info)
            result['drinkable_water_pipes']['count'] += 1
            if length is not None:
                result['drinkable_water_pipes']['total_length'] += length
        else:
            result['other_pipes']['items'].append(info)
            result['other_pipes']['count'] += 1
            if length is not None:
                result['other_pipes']['total_length'] += length

        # Update totals
        result['total_count'] += 1
        if length is not None:
            result['total_length'] += length

    return result
