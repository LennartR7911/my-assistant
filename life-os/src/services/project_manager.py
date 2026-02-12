import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from src.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for validation
class Stakeholder(BaseModel):
    naam: str
    rol: str
    email: str

class ProjectContext(BaseModel):
    project_name: str
    client: str
    status: str
    stakeholders: List[Stakeholder]
    doelstelling: str
    afspraken: str

def create_project(name: str, client: str):
    """
    Creates project structure:
    Projects/{Client}/{Name}/
        /01_Admin
        /02_Notes
        /03_Deliverables
        /01_Admin/context.yaml
    """
    base_path = Path(settings.KNOWLEDGE_BASE_PATH) / "Projects" / client / name

    subfolders = ["01_Admin", "02_Notes", "03_Deliverables"]

    try:
        # Create directories
        for folder in subfolders:
            (base_path / folder).mkdir(parents=True, exist_ok=True)

        # Create context.yaml
        context_data = {
            "project_name": name,
            "client": client,
            "status": "Active",
            "stakeholders": [
                {"naam": "...", "rol": "...", "email": "..."}
            ],
            "doelstelling": "...",
            "afspraken": "..."
        }

        # Validate with Pydantic (though dummy data)
        ProjectContext(**context_data)

        context_file = base_path / "01_Admin" / "context.yaml"
        if not context_file.exists():
            with open(context_file, "w") as f:
                yaml.dump(context_data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Project '{name}' created for client '{client}' at {base_path}")
        else:
            logger.info(f"Project '{name}' already exists.")

    except Exception as e:
        logger.error(f"Failed to create project: {e}")
