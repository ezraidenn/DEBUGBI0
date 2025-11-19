"""
Configuration management.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_dir: Path to configuration directory
        """
        if config_dir is None:
            # Default to project root/config
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        # Create config dir if not exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Load device aliases
        self.device_aliases = self._load_device_aliases()
    
    def _load_device_aliases(self) -> Dict[str, Dict[str, str]]:
        """Load device aliases from JSON file."""
        filepath = self.config_dir / "device_aliases.json"
        
        if not filepath.exists():
            # Create empty file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_device_aliases(self, aliases: Dict[str, Dict[str, str]]):
        """Save device aliases to JSON file."""
        filepath = self.config_dir / "device_aliases.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(aliases, f, indent=2, ensure_ascii=False)
    
    def get_env(self, key: str, default: str = "") -> str:
        """
        Get environment variable.
        
        Args:
            key: Environment variable name
            default: Default value
            
        Returns:
            Environment variable value
        """
        return os.getenv(key, default)
    
    @property
    def biostar_config(self) -> Dict[str, str]:
        """Get BioStar API configuration."""
        return {
            'host': self.get_env('BIOSTAR_HOST'),
            'username': self.get_env('BIOSTAR_USER'),
            'password': self.get_env('BIOSTAR_PASSWORD')
        }
    
    def get_device_alias(self, device_id: str) -> Optional[Dict[str, str]]:
        """Get alias info for a device."""
        return self.device_aliases.get(str(device_id))
    
    def set_device_alias(self, device_id: str, alias: str, location: str = "", notes: str = ""):
        """Set alias for a device."""
        self.device_aliases[str(device_id)] = {
            'alias': alias,
            'location': location,
            'notes': notes
        }
        self.save_device_aliases(self.device_aliases)
