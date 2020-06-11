#!/bin/bash

# Starting Cron
crond -f &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start Cron daemon: $status"
  exit $status
fi

# Creating the main cron
echo "
## The main script to collect the deployments to be scaled
*/3 * * * * ~/schedule_scaling/schedule_scaling.py 2>&1 >> /tmp/scaling_job.log
" | /usr/bin/crontab -

# main job log
touch /tmp/scaling_job.log
# secondary jobs log
touch /tmp/scale_activities.log

tail -f /tmp/scale_activities.log &
tail -f /tmp/scaling_job.log
