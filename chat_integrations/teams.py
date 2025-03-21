from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/teams_webhook")
async def teams_webhook_get():
    return {"status": "Teams webhook active"}

@router.post("/teams_webhook")
async def teams_webhook_post(request: Request):
    body = await request.json()
    # Dummy processing: echo received data
    return {"status": "Received message", "data": body}
