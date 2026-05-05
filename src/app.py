"""
Exercise 01 — Node Registry API

Implement a FastAPI application with the following endpoints:

GET    /health          → health check with DB status
POST   /api/nodes       → register a new node
GET    /api/nodes       → list all nodes
GET    /api/nodes/{name} → get a node by name
PUT    /api/nodes/{name} → update a node
DELETE /api/nodes/{name} → soft-delete a node (set status=inactive)

See README.md for full specification.
"""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from src import models, schemas
from src.database import engine, get_db, Base
import time

def create_tables():
    for attempt in range(10):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Could not connect to database")

create_tables()

app = FastAPI()

@app.get("/health", response_model=schemas.HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    nodes_count = db.query(models.Node).filter(models.Node.status == "active").count()
    
    return {"status": "ok", "db": db_status, "nodes_count": nodes_count}

@app.post("/api/nodes", response_model=schemas.NodeResponse, status_code=201)
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    db_node = models.Node(**node.model_dump())
    try:
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        return db_node
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Node already exists")

@app.get("/api/nodes", response_model=list[schemas.NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(models.Node).all()

@app.get("/api/nodes/{name}", response_model=schemas.NodeResponse)
def get_node(name: str, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.put("/api/nodes/{name}", response_model=schemas.NodeResponse)
def update_node(name: str, data: schemas.NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    updates = data.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(node, key, value)
    
    db.commit()
    db.refresh(node)
    return node

@app.delete("/api/nodes/{name}", status_code=204)
def delete_node(name: str, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.name == name).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    node.status = "inactive"
    db.commit()