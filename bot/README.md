# BEUSP Notification Bot

Notifies nerdy students for  any changes on
grades table using Student Portal API.
Uses **schedule** python library to schedule checks internally.
A cycle of check consists of these steps:
- Authorize students with no session.
- Fetch subscribed students.
- Request latest grades table.
- Fetch old grades table for subscribed students.
- Compare grades table using **jsondiff**.
- Notify the student asynchronously.
- Replace old grades tables with new ones.

Changing the schedule:
```
# Replace the line with yours at
# bot/process.py (Line 35)

# run job until a 18:30 today
schedule.every(1).hours.until("18:30").do(run_chain, httpc, emailc)

# run job until a 2030-01-01 18:33 today
schedule.every(1).hours.until("2030-01-01 18:33").do(run_chain, httpc, emailc)

# Schedule a job to run for the next 8 hours
schedule.every(1).hours.until(timedelta(hours=8)).do(run_chain, httpc, emailc)

# Run my_job until today 11:33:42
schedule.every(1).hours.until(time(11, 33, 42)).do(run_chain, httpc, emailc)

# run job until a specific datetime
schedule.every(1).hours.until(datetime(2020, 5, 17, 11, 36, 20)).do(run_chain, httpc, emailc)
```
Ref: https://schedule.readthedocs.io/en/stable/examples.html

[//]: # (TODO: Dockerize)