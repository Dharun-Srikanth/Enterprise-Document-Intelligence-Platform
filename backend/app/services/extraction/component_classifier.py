"""Component classification from tear-down photos using GPT-4o vision."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COMPONENT_TYPES = [
    "seat_track_assembly",
    "slide_rail_mechanism",
    "seat_frame_structure",
    "recliner_mechanism",
    "wire_spring_support",
]

MATERIAL_TYPES = [
    "cold_rolled_steel",
    "tubular_steel",
    "HSLA_steel",
    "spring_steel_wire",
    "aluminum_alloy",
]


@dataclass
class ComponentClassification:
    component_type: str
    component_confidence: float
    material: str
    material_confidence: float
    reasoning: str | None = None
    raw_response: dict | None = None


def classify_component(image_data_url: str) -> ComponentClassification:
    """
    Classify a tear-down component photo using GPT-4o vision.

    Identifies:
    1. Component type (seat track, slide rail, seat frame, recliner, wire spring)
    2. Material type (cold-rolled steel, tubular steel, HSLA, spring wire, aluminum)

    Args:
        image_data_url: Base64-encoded image data URL (data:image/jpeg;base64,...)

    Returns:
        ComponentClassification with types and confidence scores
    """
    try:
        return _vision_classify(image_data_url)
    except Exception as e:
        logger.error(f"Vision classification failed: {e}")
        return ComponentClassification(
            component_type="unknown",
            component_confidence=0.0,
            material="unknown",
            material_confidence=0.0,
            reasoning=f"Classification failed: {str(e)}",
        )


def _vision_classify(image_data_url: str) -> ComponentClassification:
    """Use GPT-4o vision to classify the component."""
    from app.services.llm_client import vision_completion_json

    prompt = """You are an automotive component engineer analyzing a tear-down photo of a seat component.

Identify the component type and likely material from this image.

Component types (pick one):
- seat_track_assembly: Linear track mechanism for seat adjustment, usually two parallel rails with cross-members and locking mechanisms
- slide_rail_mechanism: Single rail with ball bearings for smooth linear motion
- seat_frame_structure: Main structural frame of the seat, usually U-shaped or rectangular tubular/stamped steel
- recliner_mechanism: Circular gear mechanism with lever for seat back angle adjustment
- wire_spring_support: Serpentine or zigzag wire springs for seat cushion support

Material types (pick one):
- cold_rolled_steel: Smooth, matte gray finish, uniform thickness, common stamped parts
- tubular_steel: Hollow circular or rectangular cross-section tubes
- HSLA_steel: Similar to cold-rolled but may appear slightly different gauge, used in high-strength applications
- spring_steel_wire: Thin wire bent into spring shapes, high elasticity
- aluminum_alloy: Lighter color, sometimes with visible casting marks or machining lines

Return JSON:
{
  "component_type": "one of the component types above",
  "component_confidence": 0.0 to 1.0,
  "material": "one of the material types above",
  "material_confidence": 0.0 to 1.0,
  "reasoning": "brief explanation of visual features that led to this classification"
}"""

    result = vision_completion_json(
        image_data_url=image_data_url,
        prompt=prompt,
        temperature=0.1,
        max_tokens=500,
    )

    component_type = result.get("component_type", "unknown")
    material = result.get("material", "unknown")

    # Validate against known types
    if component_type not in COMPONENT_TYPES:
        logger.warning(f"Unknown component type from vision: {component_type}")
        # Find closest match
        component_type = _fuzzy_match(component_type, COMPONENT_TYPES)

    if material not in MATERIAL_TYPES:
        logger.warning(f"Unknown material type from vision: {material}")
        material = _fuzzy_match(material, MATERIAL_TYPES)

    return ComponentClassification(
        component_type=component_type,
        component_confidence=float(result.get("component_confidence", 0.5)),
        material=material,
        material_confidence=float(result.get("material_confidence", 0.5)),
        reasoning=result.get("reasoning"),
        raw_response=result,
    )


def _fuzzy_match(value: str, options: list[str]) -> str:
    """Simple fuzzy match: find the option with most common words."""
    value_words = set(value.lower().replace("_", " ").split())
    best_match = options[0]
    best_score = 0

    for opt in options:
        opt_words = set(opt.lower().replace("_", " ").split())
        score = len(value_words & opt_words)
        if score > best_score:
            best_score = score
            best_match = opt

    return best_match
