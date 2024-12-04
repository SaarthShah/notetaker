from fastapi import FastAPI, HTTPException, Request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
import pytz
import uvicorn

app = FastAPI()

# Configure the job store to use a database
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler.start()

def execute_task(task_id):
    print(f"Executing task {task_id} at {datetime.now()}")

@app.post('/schedule-task')
async def schedule_task(request: Request):
    data = await request.json()
    task_id = data.get('task_id')
    run_time = data.get('run_time')  # Expected format: 'YYYY-MM-DD HH:MM:SS'

    if not task_id or not run_time:
        raise HTTPException(status_code=400, detail="task_id and run_time are required")

    try:
        # Parse the run_time to a datetime object
        run_time = datetime.strptime(run_time, '%Y-%m-%d %H:%M:%S')
        run_time = pytz.utc.localize(run_time)  # Ensure the time is in UTC
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_time format. Use 'YYYY-MM-DD HH:MM:SS'")

    # Schedule the task
    scheduler.add_job(execute_task, 'date', run_date=run_time, args=[task_id], id=task_id)
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
