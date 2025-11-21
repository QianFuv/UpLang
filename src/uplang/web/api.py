"""REST API endpoints for web translation interface."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from uplang.web.service import TranslationService


class TranslationUpdate(BaseModel):
    """Model for translation update request."""

    translations: dict[str, str]


def create_router(resourcepack_dir: Path) -> APIRouter:
    """Create API router with translation service."""
    router = APIRouter(prefix="/api")
    service = TranslationService(resourcepack_dir)

    @router.get("/mods")
    async def get_mods() -> list[dict[str, Any]]:
        """Get all mods with translation statistics."""
        return service.get_all_mods()

    @router.get("/mods/{mod_id}")
    async def get_mod_items(mod_id: str, filter: str = "all") -> dict[str, Any]:
        """Get translation items for a specific mod.

        Args:
            mod_id: The mod identifier
            filter: Filter type - 'all', 'untranslated', or 'translated'
        """
        if filter == "untranslated":
            items = service.get_untranslated_items(mod_id)
        else:
            all_items = service.get_all_items(mod_id)
            if filter == "translated":
                items = [item for item in all_items if item["is_translated"]]
            else:
                items = all_items

        return {"mod_id": mod_id, "items": items, "total": len(items)}

    @router.put("/mods/{mod_id}/translations")
    async def update_translations(
        mod_id: str, data: TranslationUpdate
    ) -> dict[str, Any]:
        """Update translations for a mod."""
        success = service.save_translations(mod_id, data.translations)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save translations")

        return {"success": True, "message": "Translations saved successfully"}

    @router.get("/stats")
    async def get_stats() -> dict[str, Any]:
        """Get overall translation statistics."""
        mods = service.get_all_mods()
        total_keys = sum(mod["total_keys"] for mod in mods)
        total_untranslated = sum(mod["untranslated_count"] for mod in mods)
        total_translated = total_keys - total_untranslated

        return {
            "total_mods": len(mods),
            "total_keys": total_keys,
            "total_translated": total_translated,
            "total_untranslated": total_untranslated,
            "progress_percentage": round(
                (total_translated / total_keys * 100) if total_keys > 0 else 0, 2
            ),
        }

    return router
