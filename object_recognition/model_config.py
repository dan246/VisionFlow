# -*- coding: utf-8 -*-
"""
Model Configuration
Enhanced model configuration with environment variable support and validation.
"""

import os
import logging
from typing import Dict, List, Any, Optional

# Try to import supervision, fallback if not available
try:
    import supervision as sv
    from supervision.draw.color import Color
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False
    # Define basic color constants as fallback
    class Color:
        BLUE = (255, 0, 0)
        GREEN = (0, 255, 0)
        RED = (0, 0, 255)


logger = logging.getLogger(__name__)


def get_model_path(filename: str) -> str:
    """Get full model path with base directory."""
    base_dir = os.getenv('MODEL_PATH_BASE', '/app')
    return os.path.join(base_dir, filename)


def get_confidence_threshold(model_name: str, label: str = None) -> float:
    """Get confidence threshold from environment or default."""
    if label:
        env_key = f"MODEL_{model_name.upper()}_CONF_{label.upper().replace(' ', '_')}"
        return float(os.getenv(env_key, '0.6'))
    else:
        env_key = f"MODEL_{model_name.upper()}_CONF"
        return float(os.getenv(env_key, '0.5'))


# Enhanced model configuration with environment variable support
MODEL_CONFIG = {
    "model1": {
        "name": "General Detection Model",
        "description": "General purpose object detection for common objects",
        "path": [get_model_path("yolo11n.pt")],
        "conf": get_confidence_threshold("model1"),
        "enabled": os.getenv('MODEL1_ENABLED', 'true').lower() == 'true',
        "label_conf": {
            "person": get_confidence_threshold("model1", "person"),
            "bicycle": get_confidence_threshold("model1", "bicycle"),
            "car": get_confidence_threshold("model1", "car"),
            "dog": get_confidence_threshold("model1", "dog"),
            "cat": get_confidence_threshold("model1", "cat"),
        },
        "annotators": {
            "box_annotator": {
                "type": "BoxAnnotator",
                "thickness": int(os.getenv('MODEL1_BOX_THICKNESS', '2')),
                "color": None,  # Use default colors
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_thickness": int(os.getenv('MODEL1_TEXT_THICKNESS', '1')),
                "text_scale": float(os.getenv('MODEL1_TEXT_SCALE', '0.5')),
            }
        }
    },
    "model2": {
        "name": "Indoor Objects Model",
        "description": "Specialized for indoor object detection",
        "path": [get_model_path("model/yolo11n.pt")],
        "conf": get_confidence_threshold("model2"),
        "enabled": os.getenv('MODEL2_ENABLED', 'false').lower() == 'true',
        "label_conf": {
            "cat": get_confidence_threshold("model2", "cat"),
            "laptop": get_confidence_threshold("model2", "laptop"),
            "cell phone": get_confidence_threshold("model2", "cell_phone"),
            "chair": get_confidence_threshold("model2", "chair"),
            "book": get_confidence_threshold("model2", "book"),
        },
        "annotators": {
            "box_annotator": {
                "type": "BoxAnnotator",
                "thickness": int(os.getenv('MODEL2_BOX_THICKNESS', '2')),
                "color": Color.BLUE if SUPERVISION_AVAILABLE else (255, 0, 0),
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_thickness": int(os.getenv('MODEL2_TEXT_THICKNESS', '1')),
                "text_scale": float(os.getenv('MODEL2_TEXT_SCALE', '0.5')),
            }
        }
    },
    "model3": {
        "name": "Kitchen Objects Model",
        "description": "Specialized for kitchen and dining object detection",
        "path": [get_model_path("model/yolo11n.pt")],
        "conf": get_confidence_threshold("model3"),
        "enabled": os.getenv('MODEL3_ENABLED', 'false').lower() == 'true',
        "label_conf": {
            "bottle": get_confidence_threshold("model3", "bottle"),
            "cup": get_confidence_threshold("model3", "cup"),
            "fork": get_confidence_threshold("model3", "fork"),
            "knife": get_confidence_threshold("model3", "knife"),
            "spoon": get_confidence_threshold("model3", "spoon"),
        },
        "annotators": {
            "box_annotator": {
                "type": "BoxAnnotator",
                "thickness": int(os.getenv('MODEL3_BOX_THICKNESS', '2')),
                "color": Color.GREEN if SUPERVISION_AVAILABLE else (0, 255, 0),
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_thickness": int(os.getenv('MODEL3_TEXT_THICKNESS', '1')),
                "text_scale": float(os.getenv('MODEL3_TEXT_SCALE', '0.5')),
            }
        }
    },
}


def get_enabled_models() -> Dict[str, Dict[str, Any]]:
    """Get only enabled models from configuration."""
    return {
        name: config for name, config in MODEL_CONFIG.items() 
        if config.get('enabled', True)
    }


def validate_model_paths() -> List[str]:
    """Validate that all model files exist and return any missing files."""
    missing_files = []
    
    for model_name, config in MODEL_CONFIG.items():
        if not config.get('enabled', True):
            continue
            
        for path in config.get('path', []):
            if not os.path.exists(path):
                missing_files.append(f"Model {model_name}: {path}")
                logger.warning(f"Model file not found: {path}")
    
    return missing_files


def create_annotators(model_name: str) -> Dict[str, Any]:
    """Create annotators for a specific model based on configuration."""
    if not SUPERVISION_AVAILABLE:
        logger.warning("Supervision library not available. Annotators will not be created.")
        return {}
    
    config = MODEL_CONFIG.get(model_name, {})
    annotators_config = config.get("annotators", {})
    annotators = {}
    
    for annotator_name, annotator_settings in annotators_config.items():
        annotator_type = annotator_settings.get("type")
        
        try:
            if annotator_type == "BoxAnnotator":
                thickness = annotator_settings.get("thickness", 2)
                color = annotator_settings.get("color", None)
                
                if color:
                    annotators[annotator_name] = sv.BoxAnnotator(
                        thickness=thickness,
                        color=color
                    )
                else:
                    annotators[annotator_name] = sv.BoxAnnotator(thickness=thickness)
                    
            elif annotator_type == "LabelAnnotator":
                text_thickness = annotator_settings.get("text_thickness", 1)
                text_scale = annotator_settings.get("text_scale", 0.5)
                
                annotators[annotator_name] = sv.LabelAnnotator(
                    text_thickness=text_thickness,
                    text_scale=text_scale
                )
                
            logger.debug(f"Created {annotator_type} for model {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to create annotator {annotator_name} for model {model_name}: {e}")
    
    return annotators