"""
Model Manager for Tongyi Agent
Handles model switching and preference persistence
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from config import OpenRouterModels, ModelConfig, DEFAULT_CLAUDE_CONFIG


class ModelManager:
    """Manages model selection and preferences for Tongyi Agent"""

    def __init__(self, preferences_file: Optional[str] = None):
        self.preferences_file = Path(preferences_file or DEFAULT_CLAUDE_CONFIG.model_preferences_file).expanduser()
        self.preferences = self._load_preferences()
        self.available_models = OpenRouterModels.get_all_models()

    def _load_preferences(self) -> Dict[str, Any]:
        """Load model preferences from file"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_preferences(self) -> None:
        """Save model preferences to file"""
        if DEFAULT_CLAUDE_CONFIG.save_model_choices:
            try:
                # Ensure directory exists
                self.preferences_file.parent.mkdir(parents=True, exist_ok=True)

                with open(self.preferences_file, 'w') as f:
                    json.dump(self.preferences, f, indent=2)
            except IOError:
                pass  # Silently fail if can't save

    def get_current_model(self) -> str:
        """Get the currently selected model"""
        return self.preferences.get('current_model', DEFAULT_CLAUDE_CONFIG.model_name)

    def set_model(self, model_name: str) -> bool:
        """Set the current model and save preference"""
        if model_name in self.available_models:
            self.preferences['current_model'] = model_name
            self.preferences['last_changed'] = str(Path.cwd())  # Track where changed
            self._save_preferences()
            return True
        return False

    def get_model_info(self, model_name: Optional[str] = None) -> Optional[ModelConfig]:
        """Get detailed information about a model"""
        model_name = model_name or self.get_current_model()
        return self.available_models.get(model_name)

    def list_available_models(self) -> Dict[str, ModelConfig]:
        """List all available models"""
        return self.available_models.copy()

    def list_recommended_models(self) -> list[ModelConfig]:
        """List recommended models"""
        return OpenRouterModels.get_recommended_models()

    def search_models(self, query: str) -> Dict[str, ModelConfig]:
        """Search models by name, provider, or capabilities"""
        query = query.lower()
        results = {}

        for name, model in self.available_models.items():
            if (query in name.lower() or
                query in model.display_name.lower() or
                query in model.provider.lower() or
                any(query in cap.lower() for cap in model.capabilities)):
                results[name] = model

        return results

    def get_models_by_capability(self, capability: str) -> Dict[str, ModelConfig]:
        """Get models that have a specific capability"""
        capability = capability.lower()
        results = {}

        for name, model in self.available_models.items():
            if any(capability in cap.lower() for cap in model.capabilities):
                results[name] = model

        return results

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            'current_model': self.get_current_model(),
            'total_models_available': len(self.available_models),
            'providers': list(set(m.provider for m in self.available_models.values())),
            'last_changed': self.preferences.get('last_changed'),
            'preferences_file': str(self.preferences_file),
        }

    def reset_to_default(self) -> None:
        """Reset model to default"""
        self.preferences.pop('current_model', None)
        self._save_preferences()

    def export_preferences(self, file_path: str) -> bool:
        """Export preferences to a file"""
        try:
            export_data = {
                'preferences': self.preferences,
                'available_models': {
                    name: {
                        'display_name': model.display_name,
                        'provider': model.provider,
                        'context_length': model.context_length,
                        'pricing_per_mtok': model.pricing_per_mtok,
                        'capabilities': model.capabilities
                    }
                    for name, model in self.available_models.items()
                }
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except (IOError, OSError):
            return False

    def import_preferences(self, file_path: str) -> bool:
        """Import preferences from a file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            if 'preferences' in data:
                self.preferences.update(data['preferences'])
                self._save_preferences()
            return True
        except (IOError, OSError, json.JSONDecodeError):
            return False

    def validate_model(self, model_name: str) -> bool:
        """Check if a model name is valid and available"""
        return model_name in self.available_models

    def get_model_suggestion(self, use_case: str) -> Optional[ModelConfig]:
        """Get model suggestion based on use case"""
        use_case = use_case.lower()

        suggestions = {
            'coding': [OpenRouterModels.CLAUDE_35_SONNET, OpenRouterModels.MISTRRAL_CODESTRAL],
            'fast': [OpenRouterModels.CLAUDE_35_HAIKU, OpenRouterModels.CLAUDE_3_HAIKU],
            'reasoning': [OpenRouterModels.CLAUDE_3_OPUS, OpenRouterModels.CLAUDE_35_SONNET],
            'cheap': [OpenRouterModels.CLAUDE_3_HAIKU, OpenRouterModels.MISTRRAL_CODESTRAL],
            'analysis': [OpenRouterModels.CLAUDE_3_OPUS, OpenRouterModels.CLAUDE_35_SONNET],
            'multilingual': [OpenRouterModels.MISTRAL_LARGE, OpenRouterModels.QWEN_72B],
        }

        for key, models in suggestions.items():
            if key in use_case:
                for model in models:
                    if model.name in self.available_models:
                        return model

        # Default suggestion
        return OpenRouterModels.CLAUDE_35_SONNET


# Global model manager instance
model_manager = ModelManager()