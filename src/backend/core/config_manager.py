# -*- coding: utf-8 -*-
"""
Project BUKI - Configuration & Settings Manager
Decouples hardcoded catalogs, URLs, prompt styles, and keyword rules from the main app.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        
        self.backend_dir = Path(__file__).parent.parent
        self.project_root = self.backend_dir.parent.parent
        
        if config_path:
            self.config_file = Path(config_path)
        else:
            self.config_file = self.backend_dir / "config" / "settings.json"

        self.load_env()
        self.load_settings()
        self._initialized = True

    def load_env(self):
        """Loads environment variables from root .env file if present."""
        env_path = self.project_root / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            except Exception as e:
                print(f"[ConfigManager] Env load error: {e}")

    def load_settings(self):
        """Loads or reloads settings from JSON config file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(self.config_file, "r", encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)

    def reload(self):
        """Hot-reloads configuration."""
        self.load_env()
        self.load_settings()

    # --- API ENDPOINTS & KEYS ---
    @property
    def ollama_base_url(self) -> str:
        return os.getenv("OLLAMA_BASE_URL", self.data.get("api_endpoints", {}).get("ollama_base_url", "http://127.0.0.1:11434"))

    @property
    def nvidia_base_url(self) -> str:
        return os.getenv("NVIDIA_BASE_URL", self.data.get("api_endpoints", {}).get("nvidia_base_url", "https://integrate.api.nvidia.com/v1"))

    @property
    def nvidia_api_key(self) -> str:
        return os.getenv("NVIDIA_API_KEY", "")

    @property
    def gemini_base_url(self) -> str:
        return os.getenv("GEMINI_BASE_URL", self.data.get("api_endpoints", {}).get("gemini_base_url", "https://generativelanguage.googleapis.com/v1beta"))

    @property
    def gemini_api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def openrouter_base_url(self) -> str:
        return os.getenv("OPENROUTER_BASE_URL", self.data.get("api_endpoints", {}).get("openrouter_base_url", "https://openrouter.ai/api/v1"))

    @property
    def openrouter_api_key(self) -> str:
        return os.getenv("OPENROUTER_API_KEY", "")

    # --- MODEL CATALOGS ---
    @property
    def gemini_models(self) -> List[str]:
        return self.data.get("models", {}).get("gemini_cloud", [])

    @property
    def openrouter_models(self) -> List[str]:
        return self.data.get("models", {}).get("openrouter_free", [])

    @property
    def nvidia_models(self) -> List[str]:
        return self.data.get("models", {}).get("nvidia_cloud", [])

    def get_categorized_models(self, local_models: Optional[List[str]] = None) -> Dict[str, List[str]]:
        local = local_models or []
        excluded = set(self.gemini_models + self.openrouter_models + self.nvidia_models)
        filtered_local = [m for m in local if m not in excluded]

        return {
            "gemini_cloud": self.gemini_models,
            "openrouter_free": self.openrouter_models,
            "nvidia_cloud": self.nvidia_models,
            "local_ollama": filtered_local
        }

    def get_flat_models(self, local_models: Optional[List[str]] = None) -> List[str]:
        categorized = self.get_categorized_models(local_models)
        return categorized["gemini_cloud"] + categorized["openrouter_free"] + categorized["nvidia_cloud"] + categorized["local_ollama"]

    # --- DEFAULTS & ENGINES ---
    @property
    def default_persona(self) -> str:
        return self.data.get("defaults", {}).get("persona", "mesugaki")

    @property
    def default_model(self) -> str:
        return self.data.get("defaults", {}).get("model", "gemini-2.0-flash")

    @property
    def default_tts_engine(self) -> str:
        return self.data.get("defaults", {}).get("tts_engine", "gpt_sovits")

    @property
    def available_tts_engines(self) -> List[Dict[str, str]]:
        return self.data.get("available_tts_engines", [])

    # --- ACTING STYLES & EMOTION RULES ---
    def get_acting_style_prompt(self, emotion: Optional[str]) -> Optional[str]:
        if not emotion or emotion in ["auto", "default", "none"]:
            return None
        return self.data.get("acting_styles", {}).get(emotion)

    def infer_emotion_from_context(self, context_text: str) -> str:
        """Infers emotion tag from surrounding narration or inline actions using keyword rules."""
        if not context_text:
            return "default"
        
        ctx = context_text.lower()
        rules = self.data.get("emotion_keyword_rules", {})

        # Order of evaluation matters for nuanced matching
        evaluation_order = [
            "sensual", "panting", "terrified", "resigned",
            "crying", "whisper", "flustered", "smug", "tease", "angry"
        ]

        for emo in evaluation_order:
            keywords = rules.get(emo, [])
            if any(k in ctx for k in keywords):
                return emo
                
        return "default"

# Global Singleton Instance
config = ConfigManager()
