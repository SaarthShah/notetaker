from fastapi import FastAPI, HTTPException, Request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
import pytz
import uvicorn
import requests

app = FastAPI()

# Configure the job store to use a database
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def execute_task(task_id, link, headers, body):
    try:
        response = requests.post(link, headers=headers, json=body)
        print(f"Executed task with response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error executing task: {e}")
    finally:
        # Remove the task from the scheduler after execution
        try:
            scheduler.remove_job(task_id)
            print(f"Task {task_id} deleted from scheduler after execution.")
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")

@app.post('/schedule-task')
async def schedule_task(request: Request):
    data = await request.json()
    task_id = data.get('task_id')
    run_time = data.get('run_time')  # Expected format: 'YYYY-MM-DD HH:MM:SS'
    link = data.get('link')
    headers = data.get('headers', {})
    body = data.get('body', {})

    if not task_id or not run_time or not link:
        raise HTTPException(status_code=400, detail="task_id, run_time, and link are required")

    try:
        # Parse the run_time to a datetime object
        run_time = datetime.strptime(run_time, '%Y-%m-%d %H:%M:%S')
        run_time = pytz.utc.localize(run_time)  # Ensure the time is in UTC
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_time format. Use 'YYYY-MM-DD HH:MM:SS'")

    # Check if the task already exists
    existing_job = scheduler.get_job(task_id)
    if existing_job:
        # Update the existing task
        scheduler.modify_job(task_id, run_date=run_time, args=[task_id, link, headers, body])
        return {"status": "Task updated", "task_id": task_id}

    # Schedule the task
    scheduler.add_job(execute_task, 'date', run_date=run_time, args=[task_id, link, headers, body], id=task_id)
    return {"status": "Task scheduled", "task_id": task_id}

@app.delete('/delete-task')
async def delete_task(task_id: str):
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id is required")

    try:
        scheduler.remove_job(task_id)
        return {"status": "Task deleted", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8050)
