from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import detection, reports, heatmap, streaming, auth

app = FastAPI(title="Toll Vehicle Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection.router)
app.include_router(reports.router)
app.include_router(heatmap.router)
app.include_router(streaming.router)
app.include_router(auth.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Toll Vehicle Detection API is running"}
