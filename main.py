import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import ContactMessage

app = FastAPI(title="Creator Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Creator Portfolio Backend Running"}

# Health + database test
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# Public content endpoints (static for now, could be moved to DB later)
class Project(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    url: Optional[str] = None
    thumbnail: Optional[str] = None

@app.get("/api/projects", response_model=List[Project])
def get_projects():
    projects = [
        Project(
            id="storyengine",
            title="StoryEngine: Interactive Narratives",
            description="A web-based tool that blends code and storytelling to craft interactive lessons.",
            tags=["React", "FastAPI", "Education", "Storytelling"],
            url="https://example.com/storyengine"
        ),
        Project(
            id="devcasts",
            title="DevCasts: Bite-size Video Lessons",
            description="A micro-learning platform for teaching web dev through short, cinematic episodes.",
            tags=["Next.js", "MongoDB", "Video"],
            url="https://example.com/devcasts"
        ),
        Project(
            id="a11y-kit",
            title="a11y-kit: Accessible UI Toolkit",
            description="A component library that pairs accessibility-first patterns with playful motion.",
            tags=["Library", "Design Systems", "Framer Motion"],
            url="https://example.com/a11y-kit"
        )
    ]
    return projects

# Contact form endpoints (persist to MongoDB)
@app.post("/api/contact")
def submit_contact(message: ContactMessage):
    try:
        inserted_id = create_document("contactmessage", message)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contact", summary="List last contact messages (admin/demo)")
def list_contacts(limit: int = 10):
    try:
        docs = get_documents("contactmessage", limit=limit)
        # Convert ObjectId for JSON safety
        def normalize(doc):
            d = dict(doc)
            if "_id" in d and isinstance(d["_id"], ObjectId):
                d["_id"] = str(d["_id"])
            return d
        return [normalize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
