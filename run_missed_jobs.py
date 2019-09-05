import os
import time
from crontab import CronTab
from datetime import datetime
from datetime import timedelta

cron = CronTab(user='root')
scale_jobs = cron.find_comment('Scheduling_Jobs')

print("Running the Jobs of the last 5 minutes")

for job in scale_jobs:

    # print(job)

    schedule = job.schedule(date_from=datetime.now())
    schedule = str(schedule.get_prev())
    schedule = time.strptime(schedule, "%Y-%m-%d %H:%M:%S")
    retry_execution_threshold = str(datetime.now() - timedelta(minutes=5))
    retry_execution_threshold = time.strptime(retry_execution_threshold, "%Y-%m-%d %H:%M:%S.%f")

    if schedule > retry_execution_threshold:
        schedule_to_execute = str(job).split(";")[2]
        os.system(schedule_to_execute)
