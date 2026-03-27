# filepath: /home/canequero/APP975/backend/app/api/v1/endpoints/datasets.py
from fastapi import APIRouter
from app.utils_helpers import get_datasets, get_dataset_documents

router = APIRouter()

@router.get("/")
def get_all_datasets():
    return get_datasets()

@router.get("/{dataset_id}/documents")
def get_documents_for_dataset(dataset_id: str):
    return get_dataset_documents(dataset_id)
