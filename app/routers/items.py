from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Annotated, Union
from enum import Enum
import os


from app.dependencies import get_token_header

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

class Item(BaseModel):
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None

class ItemWithId(Item):
    item_id: int

fake_items_db = [
    Item(name="Plumbus", description=None, price=100, tax=None),
    Item(name="Portal Gun", description=None, price=500, tax=None)
]

@router.get("/", response_model=list[ItemWithId])
def list_items():
    return [ItemWithId(**item.dict(), item_id=idx) for idx, item in enumerate(fake_items_db)]

@router.get("/{item_id}", response_model=ItemWithId)
async def read_user_item(item_id: int):
    if 0 <= item_id < len(fake_items_db):
        item = fake_items_db[item_id]
        return ItemWithId(**item.dict(), item_id=item_id)
    return {"error": "Item not found"}

@router.put("/{item_id}", response_model=ItemWithId)
def update_item(item_id: int, item: Item):
    if 0 <= item_id < len(fake_items_db):
        fake_items_db[item_id] = item
        return ItemWithId(**item.dict(), item_id=item_id)
    return {"error": "Item not found"}

@router.post("/", response_model=ItemWithId)
async def create_item(item: Item):
    fake_items_db.append(item)
    return ItemWithId(**item.dict(), item_id=len(fake_items_db) - 1)

# Single file upload and save to disk
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    contents = await file.read()
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    return {"filename": file.filename}

# Multiple file upload
@router.post("/uploadfiles/")
async def upload_files(
    files: Annotated[
        list[UploadFile], File(description="Multiple files as UploadFile")
    ],
):
    return {"filenames": [file.filename for file in files]}
