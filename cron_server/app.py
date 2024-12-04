from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
import pytz

app = Flask(__name__)

# Configure the job store to use a database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.sqlite'
jobstores = {
    'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def execute_task(task_id):
    print(f"Executing task {task_id} at {datetime.now()}")

@app.route('/schedule-task', methods=['POST'])
def schedule_task():
    data = request.json
    task_id = data.get('task_id')
    run_time = data.get('run_time')  # Expected format: 'YYYY-MM-DD HH:MM:SS'

    if not task_id or not run_time:
        return jsonify({"error": "task_id and run_time are required"}), 400

    try:
        # Parse the run_time to a datetime object
        run_time = datetime.strptime(run_time, '%Y-%m-%d %H:%M:%S')
        run_time = pytz.utc.localize(run_time)  # Ensure the time is in UTC
    except ValueError:
        return jsonify({"error": "Invalid run_time format. Use 'YYYY-MM-DD HH:MM:SS'"}), 400

    # Schedule the task
    scheduler.add_job(execute_task, 'date', run_date=run_time, args=[task_id], id=task_id)
    return jsonify({"status": "Task scheduled", "task_id": task_id}), 200

@app.route('/delete-task', methods=['DELETE'])
def delete_task():
    task_id = request.args.get('task_id')

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    try:
        scheduler.remove_job(task_id)
        return jsonify({"status": "Task deleted", "task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run()
