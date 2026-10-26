#!/usr/bin/env python3
"""Generate model, schema, service and router for a new resource.

Usage: python add_resource.py <project-dir> <resource-name>
Example: python add_resource.py myapp item   (creates Item CRUD)
"""
import sys
from pathlib import Path

MODEL = '''from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class __C__(Base):
    __tablename__ = "__s__s"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
'''

SCHEMA = '''from pydantic import BaseModel, ConfigDict


class __C__Create(BaseModel):
    name: str


class __C__Update(BaseModel):
    name: str | None = None


class __C__Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
'''

SERVICE = '''from sqlalchemy.orm import Session

from app.models.__s__ import __C__
from app.schemas.__s__ import __C__Create, __C__Update


def list_all(db: Session) -> list[__C__]:
    return db.query(__C__).all()


def get(db: Session, id: int) -> __C__ | None:
    return db.get(__C__, id)


def create(db: Session, data: __C__Create) -> __C__:
    obj = __C__(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, obj: __C__, data: __C__Update) -> __C__:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: __C__) -> None:
    db.delete(obj)
    db.commit()
'''

ROUTER = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.__s__ import __C__Create, __C__Read, __C__Update
from app.services import __s__ as service

router = APIRouter(prefix="/__s__s", tags=["__s__s"])


@router.get("/", response_model=list[__C__Read])
def list___s__s(db: Session = Depends(get_db)):
    return service.list_all(db)


@router.post("/", response_model=__C__Read, status_code=201)
def create___s__(data: __C__Create, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("/{id}", response_model=__C__Read)
def get___s__(id: int, db: Session = Depends(get_db)):
    obj = service.get(db, id)
    if not obj:
        raise HTTPException(404, "__C__ not found")
    return obj


@router.patch("/{id}", response_model=__C__Read)
def update___s__(id: int, data: __C__Update, db: Session = Depends(get_db)):
    obj = service.get(db, id)
    if not obj:
        raise HTTPException(404, "__C__ not found")
    return service.update(db, obj, data)


@router.delete("/{id}", status_code=204)
def delete___s__(id: int, db: Session = Depends(get_db)):
    obj = service.get(db, id)
    if not obj:
        raise HTTPException(404, "__C__ not found")
    service.delete(db, obj)
'''


def render(tpl, name):
    return tpl.replace("__C__", name.capitalize()).replace("__s__", name)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, name = Path(sys.argv[1]), sys.argv[2].lower()
    app = root / "app"
    if not app.is_dir():
        raise SystemExit(f"Error: {app} not found. Run scaffold_project.py first.")

    targets = {
        app / "models" / f"{name}.py": MODEL,
        app / "schemas" / f"{name}.py": SCHEMA,
        app / "services" / f"{name}.py": SERVICE,
        app / "routers" / f"{name}.py": ROUTER,
    }
    for path, tpl in targets.items():
        if path.exists():
            print(f"Skipped (exists): {path}")
            continue
        path.write_text(render(tpl, name))
        print(f"Created {path}")

    print("\nIn app/main.py, uncomment/add these three lines in their marked spots:")
    print(f"  1) from app.models import {name} as {name}_model  # noqa: F401")
    print(f"  2) from app.routers import {name}")
    print(f'  3) app.include_router({name}.router, prefix="/api/v1")')


if __name__ == "__main__":
    main()
