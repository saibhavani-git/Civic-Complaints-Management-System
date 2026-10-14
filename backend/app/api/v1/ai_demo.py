import json

from pathlib import Path



from fastapi import APIRouter, Depends

from pydantic import BaseModel, Field



from app.core.rbac import Role, get_current_user, require_roles

from app.schemas.user import UserInDB

from research.simulation.models.model_ensemble import classify_with_model_ensemble



router = APIRouter(prefix="/ai", tags=["AI Demo"])



_DATASET = (

    Path(__file__).resolve().parents[3] / "research" / "simulation" / "data" / "simulated_classification_dataset.json"

)





@router.get("/sample-dataset")

async def sample_dataset(_=Depends(require_roles(Role.ADMIN, Role.DEPT_ADMIN))):

    if not _DATASET.exists():

        return {"samples": [], "models": []}

    return json.loads(_DATASET.read_text(encoding="utf-8"))





@router.get("/models")

async def list_models(_=Depends(get_current_user)):

    return {

        "production": {

            "id": "gemini-six-departments",

            "name": "Gemini multimodal router",

            "modality": "text + image",

            "departments": ["PWD", "SAN", "WSD", "ELEC", "TNT", "PAR"],

            "requires": "GEMINI_API_KEY in backend/.env",

        },

        "simulation_models": [

            {

                "id": "minilm-text-router",

                "name": "MiniLM text router",

                "modality": "text",

                "location": "backend/research/simulation/models/text_classifier.py",

            },

            {

                "id": "clip-vit-b32",

                "name": "CLIP ViT-B/32",

                "modality": "image",

                "location": "backend/research/simulation/models/image_classifier.py",

            },

        ],

    }





class SimulationClassifyRequest(BaseModel):

    title: str = Field(min_length=5)

    description: str = Field(min_length=20)

    image_urls: list[str] = Field(default_factory=list)





@router.post("/simulation/classify")

async def simulation_classify(

    body: SimulationClassifyRequest,

    _=Depends(require_roles(Role.ADMIN, Role.DEPT_ADMIN)),

):

    """Run research ensemble (Gemini + MiniLM + CLIP) — not used for live citizen complaints."""

    result = await classify_with_model_ensemble(body.title, body.description, body.image_urls)

    return result


