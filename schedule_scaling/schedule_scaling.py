#!/usr/bin/env python3
""" Collecting Deployments configured for Scaling """
import os
import pathlib
import json
import logging
import shutil
import pykube
import urllib.request
import resources
from crontab import CronTab
from getpass import getuser

EXECUTION_TIME = 'datetime.datetime.now().strftime("%d-%m-%Y %H:%M UTC")'
crontab_instance = CronTab(user=getuser())

def create_job_directory():
    """ This directory will hold the temp python scripts to execute the scaling jobs """
    temp__dir = '/tmp/scaling_jobs'
    if os.path.isdir(temp__dir):
        shutil.rmtree(temp__dir)
    pathlib.Path(temp__dir).mkdir(parents=True, exist_ok=True)

def clear_cron():
    """ This is needed so that if any one removes his scaling action
          it should not be trigger again """
    crontab_instance.remove_all(comment="Scheduling_Jobs")

def commit():
    try:
        crontab_instance.write()
    except Exception as e:
        print("An exception has been raised while trying to commit the crontab changes")
        print(e)

def get_kube_api():
    """ Initiating the API from Service Account or when running locally from ~/.kube/config """
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api


def deployments_to_scale():
    '''
    Getting the deployments configured for schedule scaling...
    '''
    api = get_kube_api()
    deployments = []
    scaling_dict = {}
    for namespace in list(pykube.Namespace.objects(api)):
        namespace = str(namespace)
        for deployment in resources.Deployment.objects(api).filter(namespace=namespace):
            annotations = deployment.metadata.get('annotations', {})
            f_deployment = str(namespace + '/' + str(deployment))

            schedule_actions = parse_schedules(annotations.get('zalando.org/schedule-actions', '[]'), f_deployment)

            if schedule_actions is None or len(schedule_actions) == 0:
                continue

            deployments.append([deployment.metadata['name']])
            scaling_dict[f_deployment] = schedule_actions
    if not deployments:
        logging.info('No deployment is configured for schedule scaling')

    return scaling_dict


def deploy_job_creator():
    """ Create CronJobs for configured Deployments """

    deployments__to_scale = deployments_to_scale()
    print("Deployments collected for scaling: ")
    for deploy, schedules in deployments__to_scale.items():
        deployment = deploy.split("/")[1]
        namespace = deploy.split("/")[0]
        for n in range(len(schedules)):
            schedules_n = schedules[n]
            replicas = schedules_n.get('replicas', None)
            minReplicas = schedules_n.get('minReplicas', None)
            maxReplicas = schedules_n.get('maxReplicas', None)
            schedule = schedules_n.get('schedule', None)
            print("Deployment: %s, Namespace: %s, Replicas: %s, MinReplicas: %s, MaxReplicas: %s, Schedule: %s"
                  % (deployment, namespace, replicas, minReplicas, maxReplicas, schedule))

            script_file = os.path.expanduser("~/schedule_scaling/templates/deployment_script.py")
            with open(script_file) as script:
                script = script.read()
            deployment_script = script % {
                'namespace': namespace,
                'name': deployment,
                'replicas': replicas,
                'minReplicas': minReplicas,
                'maxReplicas': maxReplicas,
                'time': EXECUTION_TIME,
            }
            i = 0
            while os.path.exists("/tmp/scaling_jobs/%s-%s.py" % (deployment, i)):
                i += 1
            script_creator = open("/tmp/scaling_jobs/%s-%s.py" % (deployment, i), "w")
            script_creator.write(deployment_script)
            script_creator.close()
            cmd = ['/usr/bin/env python', script_creator.name, '2>&1 >> /tmp/scale_activities.log']
            cmd = ' '.join(map(str, cmd))
            job = crontab_instance.new(command=cmd)
            try:
                job.setall(schedule)
                job.set_comment("Scheduling_Jobs")
            except Exception:
                print('Deployment: %s has syntax error in the schedule' % (deployment))
                job.delete()

def parse_schedules(schedules, identifier):
    try:
        return json.loads(schedules)
    except Exception as err:
        print('%s - Error in parsing JSON %s with error' % (identifier, schedules), err)
        return []

if __name__ == '__main__':
    create_job_directory()
    clear_cron()
    deploy_job_creator()
    commit()
