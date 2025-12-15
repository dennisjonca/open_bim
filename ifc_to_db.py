"""
IFC to Database parser.
Parses IFC files and stores data in SQLite database.
"""
import os
import ifcopenshell
from db_models import Project, Storey, Product, create_database


def get_product_storey_name(product):
    """
    Get the building storey (floor) name for a product.
    
    Args:
        product: IFC product element
        
    Returns:
        Storey name or None if not found
    """
    try:
        # Try to get the container through IfcRelContainedInSpatialStructure
        if hasattr(product, 'ContainedInStructure') and product.ContainedInStructure:
            for rel in product.ContainedInStructure:
                if hasattr(rel, 'RelatingStructure'):
                    structure = rel.RelatingStructure
                    # Check if it's directly in a storey
                    if structure.is_a("IfcBuildingStorey"):
                        return structure.Name or structure.LongName or f"Storey #{structure.id()}"
                    # Check if it's in a space - traverse up to find the storey
                    elif structure.is_a("IfcSpace"):
                        if hasattr(structure, 'ContainedInStructure') and structure.ContainedInStructure:
                            for space_rel in structure.ContainedInStructure:
                                if hasattr(space_rel, 'RelatingStructure'):
                                    parent = space_rel.RelatingStructure
                                    if parent.is_a("IfcBuildingStorey"):
                                        return parent.Name or parent.LongName or f"Storey #{parent.id()}"
        
        # Check through spatial decomposition
        if hasattr(product, 'Decomposes') and product.Decomposes:
            for rel in product.Decomposes:
                if hasattr(rel, 'RelatingObject'):
                    parent = rel.RelatingObject
                    if parent.is_a("IfcBuildingStorey"):
                        return parent.Name or parent.LongName or f"Storey #{parent.id()}"
    except Exception:
        pass
    
    return None


def parse_ifc_to_db(ifc_file_path, db_path='ifc_data.db'):
    """
    Parse an IFC file and store its data in the database.
    
    Args:
        ifc_file_path: Path to the IFC file
        db_path: Path to SQLite database file
        
    Returns:
        Project object or None on error
    """
    # Validate file exists
    if not os.path.exists(ifc_file_path):
        print(f"Error: File not found: {ifc_file_path}")
        return None
    
    print(f"\nParsing IFC file: {ifc_file_path}")
    
    try:
        # Open IFC file
        ifc_file = ifcopenshell.open(ifc_file_path)
        
        # Create database session
        engine, Session = create_database(db_path)
        session = Session()
        
        # Check if project already exists
        existing_project = session.query(Project).filter_by(file_path=ifc_file_path).first()
        if existing_project:
            print(f"Project already exists in database. Deleting old data...")
            session.delete(existing_project)
            session.commit()
        
        # Get project information
        projects = ifc_file.by_type("IfcProject")
        if projects:
            project_ifc = projects[0]
            project_name = project_ifc.Name or os.path.basename(ifc_file_path)
            project_desc = project_ifc.Description if hasattr(project_ifc, 'Description') else None
        else:
            project_name = os.path.basename(ifc_file_path)
            project_desc = None
        
        # Create project in database
        project = Project(
            name=project_name,
            description=project_desc,
            ifc_schema=ifc_file.schema,
            file_path=ifc_file_path
        )
        session.add(project)
        session.flush()  # Get project.id
        
        print(f"Created project: {project_name}")
        
        # Parse and store storeys
        storey_map = {}  # Map storey name to database Storey object
        storeys_ifc = ifc_file.by_type("IfcBuildingStorey")
        
        for storey_ifc in storeys_ifc:
            storey_name = storey_ifc.Name or storey_ifc.LongName or f"Storey #{storey_ifc.id()}"
            elevation = storey_ifc.Elevation if hasattr(storey_ifc, 'Elevation') and storey_ifc.Elevation is not None else None
            
            storey = Storey(
                project_id=project.id,
                name=storey_name,
                elevation=elevation
            )
            session.add(storey)
            session.flush()  # Get storey.id
            storey_map[storey_name] = storey
        
        print(f"Created {len(storey_map)} storeys")
        
        # Parse and store products
        products_ifc = ifc_file.by_type("IfcProduct")
        product_count = 0
        unassigned_count = 0
        
        for product_ifc in products_ifc:
            ifc_type = product_ifc.is_a()
            global_id = product_ifc.GlobalId if hasattr(product_ifc, 'GlobalId') else None
            name = product_ifc.Name if hasattr(product_ifc, 'Name') else None
            
            # Get storey for this product
            storey_name = get_product_storey_name(product_ifc)
            storey = storey_map.get(storey_name) if storey_name else None
            
            if not storey:
                unassigned_count += 1
            
            product = Product(
                project_id=project.id,
                storey_id=storey.id if storey else None,
                ifc_type=ifc_type,
                global_id=global_id,
                name=name
            )
            session.add(product)
            product_count += 1
        
        # Commit all changes
        session.commit()
        
        print(f"Created {product_count} products ({unassigned_count} unassigned to floors)")
        print(f"Successfully parsed IFC file to database: {db_path}")
        
        session.close()
        return project
        
    except Exception as e:
        print(f"Error parsing IFC file: {e}")
        import traceback
        traceback.print_exc()
        return None
