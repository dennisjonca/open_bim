"""
Query functions for IFC database.
Provides various query operations for analyzing IFC data.
"""
from sqlalchemy import func, case
from db_models import Project, Storey, Product, create_database


def get_session(db_path='ifc_data.db'):
    """Get a database session."""
    engine, Session = create_database(db_path)
    return Session()


def count_objects_on_floor(ifc_type, floor_name, db_path='ifc_data.db'):
    """
    Count how many objects of a specific type are on a given floor.
    
    Args:
        ifc_type: IFC object type (e.g., 'IfcWall', 'IfcDoor')
        floor_name: Name of the floor/storey
        db_path: Path to SQLite database file
        
    Returns:
        Count of objects
    """
    session = get_session(db_path)
    
    try:
        count = session.query(Product).join(Storey).filter(
            Product.ifc_type == ifc_type,
            Storey.name == floor_name
        ).count()
        return count
    finally:
        session.close()


def get_all_object_types_on_floor(floor_name, db_path='ifc_data.db'):
    """
    Get all object types and their counts on a specific floor.
    
    Args:
        floor_name: Name of the floor/storey
        db_path: Path to SQLite database file
        
    Returns:
        List of tuples (object_type, count) sorted by count descending
    """
    session = get_session(db_path)
    
    try:
        results = session.query(
            Product.ifc_type,
            func.count(Product.id).label('count')
        ).join(Storey).filter(
            Storey.name == floor_name
        ).group_by(Product.ifc_type).order_by(func.count(Product.id).desc()).all()
        
        return [(row.ifc_type, row.count) for row in results]
    finally:
        session.close()


def get_all_floors(db_path='ifc_data.db'):
    """
    Get all floors/storeys in the database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of Storey objects sorted by elevation
    """
    session = get_session(db_path)
    
    try:
        # Order by elevation, putting NULL values at the end
        # SQLite doesn't support NULLS LAST, so use CASE statement
        storeys = session.query(Storey).order_by(
            case((Storey.elevation.is_(None), 1), else_=0),
            Storey.elevation.asc()
        ).all()
        return [(s.name, s.elevation) for s in storeys]
    finally:
        session.close()


def get_object_type_counts(db_path='ifc_data.db'):
    """
    Get counts of all object types across all floors.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of tuples (object_type, count) sorted by count descending
    """
    session = get_session(db_path)
    
    try:
        results = session.query(
            Product.ifc_type,
            func.count(Product.id).label('count')
        ).group_by(Product.ifc_type).order_by(func.count(Product.id).desc()).all()
        
        return [(row.ifc_type, row.count) for row in results]
    finally:
        session.close()


def get_floor_summary(db_path='ifc_data.db'):
    """
    Get summary of all floors with total object counts.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of tuples (floor_name, elevation, object_count)
    """
    session = get_session(db_path)
    
    try:
        # Order by elevation, putting NULL values at the end
        # SQLite doesn't support NULLS LAST, so use CASE statement
        results = session.query(
            Storey.name,
            Storey.elevation,
            func.count(Product.id).label('count')
        ).outerjoin(Product).group_by(
            Storey.id, Storey.name, Storey.elevation
        ).order_by(
            case((Storey.elevation.is_(None), 1), else_=0),
            Storey.elevation.asc()
        ).all()
        
        return [(row.name, row.elevation, row.count) for row in results]
    finally:
        session.close()


def get_products_by_type_and_floor(ifc_type, floor_name=None, db_path='ifc_data.db'):
    """
    Get detailed product information by type and optionally by floor.
    
    Args:
        ifc_type: IFC object type (e.g., 'IfcWall')
        floor_name: Optional floor name to filter by
        db_path: Path to SQLite database file
        
    Returns:
        List of tuples (product_name, floor_name, global_id)
    """
    session = get_session(db_path)
    
    try:
        query = session.query(
            Product.name,
            Storey.name.label('floor_name'),
            Product.global_id
        ).outerjoin(Storey).filter(Product.ifc_type == ifc_type)
        
        if floor_name:
            query = query.filter(Storey.name == floor_name)
        
        results = query.all()
        return [(row.name, row.floor_name, row.global_id) for row in results]
    finally:
        session.close()


def get_unassigned_products(db_path='ifc_data.db'):
    """
    Get products that are not assigned to any floor.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        List of tuples (object_type, count)
    """
    session = get_session(db_path)
    
    try:
        # Use is_(None) instead of == None for proper NULL comparison in SQLAlchemy.
        # This generates correct SQL "IS NULL" instead of "= NULL" which doesn't work.
        results = session.query(
            Product.ifc_type,
            func.count(Product.id).label('count')
        ).filter(Product.storey_id.is_(None)).group_by(
            Product.ifc_type
        ).order_by(func.count(Product.id).desc()).all()
        
        return [(row.ifc_type, row.count) for row in results]
    finally:
        session.close()


def get_project_info(db_path='ifc_data.db'):
    """
    Get information about the project in the database.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Dictionary with project information or None
    """
    session = get_session(db_path)
    
    try:
        project = session.query(Project).first()
        if project:
            return {
                'name': project.name,
                'description': project.description,
                'ifc_schema': project.ifc_schema,
                'file_path': project.file_path
            }
        return None
    finally:
        session.close()
