#!/bin/bash

LOG_DIR=/var/log/kubernetes/scaling

if [ ! -e ${LOG_DIR} ]; then
  mkdir -p ${LOG_DIR}
fi

export SCALING_JOB_LOG=${LOG_DIR}/scalingjob.log
export SCALING_ACTIVITIES_LOG=${LOG_DIR}/scale_activities.log

if [ ! -e ${SCALING_JOB_LOG} ]; then
  touch ${SCALING_JOB_LOG}
fi

if [ ! -e ${SCALING_ACTIVITIES_LOG} ]; then
  touch ${SCALING_ACTIVITIES_LOG}
fi

# Starting Cron
/usr/sbin/cron -f &

cron_pid=$!
echo "cron_pid: $cron_pid"

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
/usr/bin/python /root/schedule_scaling/schedule_scaling.py >> ${SCALING_JOB_LOG} 2>&1

# Creating the main cron

echo "
## The main script to collect the deployments to be scaled ##
*/3 * * * * . /root/.profile; /usr/bin/python /root/schedule_scaling/schedule_scaling.py ${SCALING_ACTIVITIES_LOG} >> ${SCALING_JOB_LOG} 2>&1
" | /usr/bin/crontab -

# Run once at the startup of container
/usr/bin/python /root/run_missed_jobs.py >> ${SCALING_ACTIVITIES_LOG}

trap 'jobs -p | xargs kill; sleep 10; echo === Finish this script ===; exit 0' SIGTERM

# Getting the Scaling Activities
tail -f ${SCALING_ACTIVITIES_LOG} ${SCALING_JOB_LOG}

