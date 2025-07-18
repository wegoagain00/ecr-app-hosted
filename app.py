from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# File to store tasks (persistent storage without database)
TASKS_FILE = 'tasks.json'

def load_tasks():
    """Load tasks from JSON file"""
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_tasks(tasks):
    """Save tasks to JSON file"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        return True
    except:
        return False

# In-memory storage for current session
tasks = load_tasks()

@app.route('/')
def index():
    """Main page with task list"""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    # Sort tasks by created date (newest first)
    sorted_tasks = sorted(tasks, key=lambda x: x['created_at'], reverse=True)
    return jsonify(sorted_tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    data = request.get_json()
    
    if not data or not data.get('title', '').strip():
        return jsonify({'error': 'Task title is required'}), 400
    
    new_task = {
        'id': str(uuid.uuid4()),
        'title': data['title'].strip(),
        'description': data.get('description', '').strip(),
        'priority': data.get('priority', 'medium'),
        'category': data.get('category', 'general'),
        'completed': False,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    return jsonify(new_task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    data = request.get_json()
    
    for task in tasks:
        if task['id'] == task_id:
            task['title'] = data.get('title', task['title']).strip()
            task['description'] = data.get('description', task['description']).strip()
            task['priority'] = data.get('priority', task['priority'])
            task['category'] = data.get('category', task['category'])
            task['completed'] = data.get('completed', task['completed'])
            task['updated_at'] = datetime.now().isoformat()
            
            save_tasks(tasks)
            return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    global tasks
    tasks = [task for task in tasks if task['id'] != task_id]
    save_tasks(tasks)
    return jsonify({'message': 'Task deleted successfully'})

@app.route('/api/tasks/<task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion status"""
    for task in tasks:
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            task['updated_at'] = datetime.now().isoformat()
            save_tasks(tasks)
            return jsonify(task)
    
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get task statistics"""
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task['completed'])
    pending_tasks = total_tasks - completed_tasks
    
    # Count by priority
    priority_counts = {}
    for task in tasks:
        priority = task['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Count by category
    category_counts = {}
    for task in tasks:
        category = task['category']
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
        'priority_distribution': priority_counts,
        'category_distribution': category_counts
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'tasks_count': len(tasks)
    })

@app.route('/api/export', methods=['GET'])
def export_tasks():
    """Export tasks as JSON"""
    return jsonify({
        'export_date': datetime.now().isoformat(),
        'tasks': tasks
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)