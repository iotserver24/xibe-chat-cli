#!/usr/bin/env python3
"""
XIBE-CHAT Analytics Server
Collects usage statistics from XIBE-CHAT CLI installations
"""

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os
import sqlite3
from collections import defaultdict
import uuid

app = Flask(__name__)

# Database file
DB_FILE = "xibe_analytics.db"

def init_database():
    """Initialize the SQLite database for analytics."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            version TEXT NOT NULL,
            platform TEXT NOT NULL,
            python_version TEXT NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_usage INTEGER DEFAULT 1
        )
    ''')
    
    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_machine_id():
    """Generate or retrieve machine ID."""
    machine_id_file = "machine_id.txt"
    if os.path.exists(machine_id_file):
        with open(machine_id_file, 'r') as f:
            return f.read().strip()
    else:
        machine_id = str(uuid.uuid4())
        with open(machine_id_file, 'w') as f:
            f.write(machine_id)
        return machine_id

@app.route('/')
def home():
    """Home page with analytics dashboard."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get total unique users
    cursor.execute("SELECT COUNT(DISTINCT machine_id) FROM sessions")
    total_users = cursor.fetchone()[0]
    
    # Get active users (last 24 hours)
    cursor.execute("""
        SELECT COUNT(DISTINCT machine_id) FROM sessions 
        WHERE last_seen > datetime('now', '-1 day')
    """)
    active_users_24h = cursor.fetchone()[0]
    
    # Get active users (last 7 days)
    cursor.execute("""
        SELECT COUNT(DISTINCT machine_id) FROM sessions 
        WHERE last_seen > datetime('now', '-7 days')
    """)
    active_users_7d = cursor.fetchone()[0]
    
    # Get version distribution
    cursor.execute("""
        SELECT version, COUNT(*) FROM sessions 
        GROUP BY version ORDER BY COUNT(*) DESC
    """)
    version_stats = cursor.fetchall()
    
    # Get platform distribution
    cursor.execute("""
        SELECT platform, COUNT(*) FROM sessions 
        GROUP BY platform ORDER BY COUNT(*) DESC
    """)
    platform_stats = cursor.fetchall()
    
    # Get recent events
    cursor.execute("""
        SELECT event_type, COUNT(*) FROM events 
        WHERE timestamp > datetime('now', '-24 hours')
        GROUP BY event_type ORDER BY COUNT(*) DESC
    """)
    recent_events = cursor.fetchall()
    
    conn.close()
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>XIBE-CHAT Analytics Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: #2a2a2a; padding: 20px; margin: 20px 0; border-radius: 8px; border: 1px solid #444; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
            .stat {{ background: #333; padding: 15px; border-radius: 6px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #00e5ff; }}
            .stat-label {{ color: #ccc; margin-top: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #444; }}
            th {{ background: #333; color: #00e5ff; }}
            h1 {{ color: #00e5ff; text-align: center; }}
            h2 {{ color: #00ccff; border-bottom: 2px solid #00ccff; padding-bottom: 5px; }}
            .refresh {{ background: #00e5ff; color: #000; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            .refresh:hover {{ background: #00ccff; }}
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <h1>🤖 XIBE-CHAT Analytics Dashboard</h1>
            <p style="text-align: center; color: #ccc;">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: 30s</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{total_users}</div>
                    <div class="stat-label">Total Unique Users</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{active_users_24h}</div>
                    <div class="stat-label">Active (24h)</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{active_users_7d}</div>
                    <div class="stat-label">Active (7 days)</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{sum(count for _, count in recent_events)}</div>
                    <div class="stat-label">Events (24h)</div>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 Version Distribution</h2>
                <table>
                    <tr><th>Version</th><th>Users</th><th>Percentage</th></tr>
    """
    
    total_sessions = sum(count for _, count in version_stats)
    for version, count in version_stats:
        percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
        dashboard_html += f"<tr><td>{version}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    
    dashboard_html += """
                </table>
            </div>
            
            <div class="card">
                <h2>💻 Platform Distribution</h2>
                <table>
                    <tr><th>Platform</th><th>Users</th><th>Percentage</th></tr>
    """
    
    for platform, count in platform_stats:
        percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
        dashboard_html += f"<tr><td>{platform}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    
    dashboard_html += """
                </table>
            </div>
            
            <div class="card">
                <h2>⚡ Recent Activity (24h)</h2>
                <table>
                    <tr><th>Event Type</th><th>Count</th></tr>
    """
    
    for event_type, count in recent_events:
        dashboard_html += f"<tr><td>{event_type}</td><td>{count}</td></tr>"
    
    dashboard_html += """
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="refresh" onclick="location.reload()">🔄 Refresh Dashboard</button>
            </div>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/track', methods=['POST'])
def track_event():
    """Track user events and sessions."""
    try:
        data = request.get_json()
        
        # Extract data
        machine_id = data.get('machine_id')
        version = data.get('version', 'unknown')
        platform = data.get('platform', 'unknown')
        python_version = data.get('python_version', 'unknown')
        event_type = data.get('event_type', 'session')
        event_data = data.get('event_data', '{}')
        
        if not machine_id:
            return jsonify({'error': 'machine_id required'}), 400
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if session exists
        cursor.execute("SELECT id FROM sessions WHERE machine_id = ?", (machine_id,))
        session = cursor.fetchone()
        
        if session:
            session_id = session[0]
            # Update existing session
            cursor.execute("""
                UPDATE sessions 
                SET last_seen = CURRENT_TIMESTAMP, total_usage = total_usage + 1
                WHERE machine_id = ?
            """, (machine_id,))
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO sessions (id, machine_id, version, platform, python_version)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, machine_id, version, platform, python_version))
        
        # Log event
        cursor.execute("""
            INSERT INTO events (session_id, event_type, event_data)
            VALUES (?, ?, ?)
        """, (session_id, event_type, json.dumps(event_data)))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Event tracked successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get analytics statistics as JSON."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get total unique users
    cursor.execute("SELECT COUNT(DISTINCT machine_id) FROM sessions")
    total_users = cursor.fetchone()[0]
    
    # Get active users (last 24 hours)
    cursor.execute("""
        SELECT COUNT(DISTINCT machine_id) FROM sessions 
        WHERE last_seen > datetime('now', '-1 day')
    """)
    active_users_24h = cursor.fetchone()[0]
    
    # Get version distribution
    cursor.execute("""
        SELECT version, COUNT(*) FROM sessions 
        GROUP BY version ORDER BY COUNT(*) DESC
    """)
    version_stats = dict(cursor.fetchall())
    
    # Get platform distribution
    cursor.execute("""
        SELECT platform, COUNT(*) FROM sessions 
        GROUP BY platform ORDER BY COUNT(*) DESC
    """)
    platform_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'active_users_24h': active_users_24h,
        'version_distribution': version_stats,
        'platform_distribution': platform_stats,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    init_database()
    print("🤖 XIBE-CHAT Analytics Server Starting...")
    print("📊 Dashboard: http://localhost:5000")
    print("📡 API: http://localhost:5000/track")
    print("📈 Stats: http://localhost:5000/api/stats")
    
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=False)
