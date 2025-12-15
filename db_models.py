"""
Database models for storing IFC data.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Project(Base):
    """Represents an IFC project/building."""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    ifc_schema = Column(String)
    file_path = Column(String, nullable=False, unique=True)
    
    # Relationships
    storeys = relationship("Storey", back_populates="project", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(name='{self.name}', file='{self.file_path}')>"


class Storey(Base):
    """Represents a building storey (floor)."""
    __tablename__ = 'storeys'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False)
    elevation = Column(Float)
    
    # Relationships
    project = relationship("Project", back_populates="storeys")
    products = relationship("Product", back_populates="storey")
    
    def __repr__(self):
        elev_str = f", elevation={self.elevation}" if self.elevation is not None else ""
        return f"<Storey(name='{self.name}'{elev_str})>"


class Product(Base):
    """Represents an IFC product/element."""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    storey_id = Column(Integer, ForeignKey('storeys.id'))
    ifc_type = Column(String, nullable=False)
    global_id = Column(String)
    name = Column(String)
    
    # Relationships
    project = relationship("Project", back_populates="products")
    storey = relationship("Storey", back_populates="products")
    
    def __repr__(self):
        storey_info = f", storey={self.storey.name}" if self.storey else ""
        return f"<Product(type='{self.ifc_type}'{storey_info})>"


def create_database(db_path='ifc_data.db'):
    """
    Create database and tables.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Tuple of (engine, Session class)
    """
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
