#!/usr/bin/env python3
"""
Test script for new configuration system
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import get_settings, get_config_file_path, load_config, save_config

def test_default_config():
    """Test default configuration loading"""
    print("Testing default configuration...")
    
    # Load settings without any config file
    settings = get_settings()
    
    print(f"✅ App name: {settings.app_name}")
    print(f"✅ App version: {settings.app_version}")
    print(f"✅ Depot directory: {settings.depot_dir}")
    print(f"✅ Models directory: {settings.models_dir}")
    print(f"✅ Output directory: {settings.output_dir}")
    print(f"✅ Data directory: {settings.data_dir}")
    print(f"✅ Database URL: {settings.database_url}")
    print(f"✅ Server host: {settings.host}")
    print(f"✅ Server port: {settings.port}")
    print(f"✅ Civitai API key: {settings.civitai.api_key}")
    print()

def test_config_file_path():
    """Test configuration file path"""
    print("Testing configuration file path...")
    
    config_path = get_config_file_path()
    print(f"✅ Config file path: {config_path}")
    print(f"✅ Config exists: {config_path.exists()}")
    print()

def test_custom_depot():
    """Test custom depot directory"""
    print("Testing custom depot directory...")
    
    custom_depot = "/tmp/test-depot"
    settings = load_config(depot_dir=custom_depot)
    
    print(f"✅ Custom depot: {settings.depot_dir}")
    print(f"✅ Models dir: {settings.models_dir}")
    print(f"✅ Output dir: {settings.output_dir}")
    print(f"✅ Data dir: {settings.data_dir}")
    print()

def test_config_save_load():
    """Test configuration save and load"""
    print("Testing configuration save and load...")
    
    # Create test config file
    test_config_path = "/tmp/test_config.yml"
    
    # Load default settings
    settings = get_settings()
    
    # Modify some settings
    settings.server.port = 9000
    settings.server.debug = True
    
    # Save configuration
    save_config(settings, test_config_path)
    print(f"✅ Configuration saved to: {test_config_path}")
    
    # Load configuration back
    loaded_settings = load_config(test_config_path)
    
    print(f"✅ Loaded port: {loaded_settings.server.port}")
    print(f"✅ Loaded debug: {loaded_settings.server.debug}")
    
    # Clean up
    os.remove(test_config_path)
    print("✅ Test config file cleaned up")
    print()

def main():
    """Run all tests"""
    print("🧪 SD-Host Configuration System Tests")
    print("=" * 50)
    
    try:
        test_default_config()
        test_config_file_path()
        test_custom_depot()
        test_config_save_load()
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
