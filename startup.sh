#!/bin/bash

# Starting Cron
/usr/sbin/cron -f &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start Cron daemon: $status"
  exit $status
fi

# Exporting Env variables
env >> /etc/environment
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to export env variables: $status"
  exit $status
fi

# Running the main Script at the beginning
/usr/bin/python /root/schedule_scaling/schedule_scaling.py 

# Creating the main cron

echo "
## The main script to collect the deployments & stacksets to be scaled##
*/3 * * * * . /root/.profile; /usr/bin/python /root/schedule_scaling/schedule_scaling.py 2>&1 | tee -a /tmp/scalingjob.log
" | /usr/bin/crontab -

# Run once at the startup of container
/usr/bin/python /root/run_missed_jobs.py  >> /tmp/scale_activities.log

# Getting the Scaling Activities
touch /tmp/scalingjob.log
touch /tmp/scale_activities.log
tail -f /tmp/scale_activities.log &
tail -f /tmp/scalingjob.log
