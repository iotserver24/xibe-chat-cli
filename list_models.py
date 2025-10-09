#!/usr/bin/env python3
"""
Model listing utility for AI CLI
Shows available text and image models from the API
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_text_models():
    """List available text generation models."""
    try:
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        url = f"{text_api_url}/models"
        
        headers = {"User-Agent": "AI-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        print("🤖 Available Text Models:")
        print("=" * 40)
        
        # Filter out audio and uncensored models
        filtered_models = []
        for model in models:
            if isinstance(model, dict):
                # Skip audio models and uncensored models
                if (model.get('audio', False) or 
                    model.get('uncensored', False) or
                    model.get('name') in ['openai-audio', 'evil', 'unity']):
                    continue
                
                name = model.get('name', 'unknown')
                description = model.get('description', 'No description')
                tier = model.get('tier', 'unknown')
                
                filtered_models.append({
                    'name': name,
                    'description': description,
                    'tier': tier
                })
        
        # Sort by tier (anonymous first, then seed)
        filtered_models.sort(key=lambda x: (x['tier'] != 'anonymous', x['name']))
        
        for model in filtered_models:
            tier_indicator = "🆓" if model['tier'] == 'anonymous' else "🔑"
            print(f"  {tier_indicator} {model['name']}")
            print(f"    {model['description']}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error fetching text models: {e}")
        print("💡 Default text models: openai, mistral, gemini")
        print()

def list_image_models():
    """List available image generation models."""
    try:
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai')
        url = f"{image_api_url}/models"
        
        headers = {"User-Agent": "AI-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        print("🎨 Available Image Models:")
        print("=" * 40)
        
        if isinstance(models, list):
            for model in models:
                if model == 'nanobanana':
                    print(f"  • {model} (requires input image for editing)")
                else:
                    print(f"  • {model}")
        elif isinstance(models, dict):
            for key, value in models.items():
                if key == 'nanobanana':
                    print(f"  • {key} (requires input image for editing)")
                else:
                    print(f"  • {key}")
                if isinstance(value, dict) and 'description' in value:
                    print(f"    Description: {value['description']}")
        
        print()
        print("💡 Note: Models change daily - check API directly for current availability")
        print()
        
    except Exception as e:
        print(f"❌ Error fetching image models: {e}")
        print("💡 Note: Models change daily - check API directly for current availability")
        print("💡 Default image models: flux, kontext, turbo, nanobanana, gptimage")
        print()

def main():
    """Main function to list all available models."""
    print("AI CLI - Model Listing Utility")
    print("=" * 50)
    print()
    
    list_text_models()
    list_image_models()
    
    print("📝 Usage in .env file:")
    print("TEXT_MODEL=model_name")
    print("IMAGE_MODEL=model_name")
    print()
    print("💡 Run 'python ai_cli.py' to use these models!")

if __name__ == "__main__":
    main()
