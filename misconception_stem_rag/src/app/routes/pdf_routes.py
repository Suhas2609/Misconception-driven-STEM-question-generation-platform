from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services import pdf_service

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, int | str]:
    destination_dir = Path("data/pdfs")
    destination_dir.mkdir(parents=True, exist_ok=True)
    file_path = destination_dir / file.filename

    try:
        contents = await file.read()
        file_path.write_bytes(contents)
        chunks = pdf_service.process_pdf(str(file_path))
    except Exception as exc:  # pragma: no cover - surfaced via HTTP details
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"filename": file.filename, "num_chunks": len(chunks)}
