#!/usr/bin/env python3
"""
XIBE-CHAT Analytics Client
Tracks usage statistics and sends to analytics server
"""

import os
import platform
import json
import requests
import threading
import time
from datetime import datetime
from pathlib import Path

# Analytics configuration
ANALYTICS_ENABLED = True
ANALYTICS_SERVER_URL = "https://cli-dash.xibe.app"  # Your deployed analytics dashboard
ANALYTICS_TIMEOUT = 5  # seconds

def get_machine_id():
    """Get or create unique machine identifier."""
    config_dir = Path.home() / ".xibe_chat"
    config_dir.mkdir(exist_ok=True)
    
    machine_id_file = config_dir / "machine_id"
    
    if machine_id_file.exists():
        try:
            return machine_id_file.read_text().strip()
        except:
            pass
    
    # Generate new machine ID
    import uuid
    machine_id = str(uuid.uuid4())
    
    try:
        machine_id_file.write_text(machine_id)
    except:
        pass  # Fail silently if can't write
    
    return machine_id

def get_system_info():
    """Get system information for analytics."""
    return {
        'platform': platform.system(),
        'platform_version': platform.release(),
        'python_version': platform.python_version(),
        'architecture': platform.machine(),
        'hostname': platform.node()
    }

def send_analytics(event_type, event_data=None, version=None):
    """Send analytics data to server (non-blocking)."""
    if not ANALYTICS_ENABLED:
        return
    
    def _send():
        try:
            payload = {
                'machine_id': get_machine_id(),
                'version': version or "0.7.0",
                'event_type': event_type,
                'event_data': event_data or {},
                'timestamp': datetime.now().isoformat(),
                **get_system_info()
            }
            
            response = requests.post(
                f"{ANALYTICS_SERVER_URL}/track",
                json=payload,
                timeout=ANALYTICS_TIMEOUT,
                headers={'User-Agent': 'XIBE-CHAT-CLI/0.7.0'}
            )
            
            if response.status_code == 200:
                pass  # Silent tracking - no user feedback
            
        except Exception as e:
            # Fail silently - don't break the user experience
            pass
    
    # Send in background thread
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

def track_session_start():
    """Track session start event."""
    send_analytics('session_start', {
        'startup_time': datetime.now().isoformat()
    })

def track_text_generation(model, message_length, conversation_length):
    """Track text generation event."""
    send_analytics('text_generated', {
        'model': model,
        'message_length': message_length,
        'conversation_length': conversation_length
    })

def track_image_generation(model, prompt_length):
    """Track image generation event."""
    send_analytics('image_generated', {
        'model': model,
        'prompt_length': prompt_length
    })

def track_agent_mode(task_type, session_type=None):
    """Track agent mode usage."""
    send_analytics('agent_mode', {
        'task_type': task_type,
        'session_type': session_type
    })

def track_command_usage(command):
    """Track command usage."""
    send_analytics('command_used', {
        'command': command
    })

def track_update_check(latest_version, status):
    """Track update check events."""
    send_analytics('update_check', {
        'latest_version': latest_version,
        'status': status,
        'current_version': "0.7.0"
    })

def track_error(error_type, error_message):
    """Track error events."""
    send_analytics('error_occurred', {
        'error_type': error_type,
        'error_message': error_message[:200]  # Limit length
    })

def track_feature_usage(feature_name, feature_data=None):
    """Track feature usage."""
    send_analytics('feature_used', {
        'feature_name': feature_name,
        'feature_data': feature_data or {}
    })

# Configuration functions
def enable_analytics():
    """Enable analytics tracking."""
    global ANALYTICS_ENABLED
    ANALYTICS_ENABLED = True

def disable_analytics():
    """Disable analytics tracking."""
    global ANALYTICS_ENABLED
    ANALYTICS_ENABLED = False

def set_analytics_server_url(url):
    """Set analytics server URL."""
    global ANALYTICS_SERVER_URL
    ANALYTICS_SERVER_URL = url.rstrip('/')

def get_analytics_status():
    """Get current analytics status."""
    return {
        'enabled': ANALYTICS_ENABLED,
        'server_url': ANALYTICS_SERVER_URL,
        'machine_id': get_machine_id() if ANALYTICS_ENABLED else None
    }
