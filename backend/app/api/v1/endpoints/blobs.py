from fastapi import APIRouter, Query
from app.utils.ai_services import AzureServices

router_folders = APIRouter()
router_files = APIRouter()
blob = AzureServices.AzureBlobStorage()


@router_folders.get("/list_folders")
def get_folders():
    blobs = blob.list_blobs()
    carpetas = []
    for b in blobs:
        carp = b.split("/")[0]
        carpetas.append(carp)
    final_list = sorted(set(carpetas))
    return final_list


@router_files.get("/list_files/")
def get_files(bloque: list[str] = Query(...)):
    all_files = []
    for folder in bloque:
        files = blob.list_blobs(prefix=f"{folder}/")
        for file in files:
            file_name = file.split("/")[-1]
            all_files.append(file_name)
    return all_files
