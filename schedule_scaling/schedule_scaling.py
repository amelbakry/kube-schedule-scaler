""" Collecting Deployments configured for Scaling """
import os
import pathlib
import json
import logging
import shutil
from kubernetes import client, config
import re
import urllib.request
from crontab import CronTab
import datetime

EXECUTION_TIME = 'datetime.datetime.now().strftime("%d-%m-%Y %H:%M UTC")'
schedule_actions_annotation = 'zalando.org/schedule-actions'

def create_job_directory():
    """ This directory will hold the temp python scripts to execute the scaling jobs """
    temp__dir = '/tmp/scaling_jobs'
    if os.path.isdir(temp__dir):
        shutil.rmtree(temp__dir)
    pathlib.Path(temp__dir).mkdir(parents=True, exist_ok=True)


def clear_cron():
    """ This is needed so that if any one removes his scaling action
          it should not be trigger again """
    my_cron = CronTab(user='root')
    my_cron.remove_all(comment="Scheduling_Jobs")
    my_cron.write()

def deployments_for_scale():
    '''
    Getting the deployments configured for schedule scaling...
    '''
    v1 = client.AppsV1Api()
    scaling_dict = {}
    deployments = v1.list_deployment_for_all_namespaces(watch=False)

    for i in deployments.items:
        if schedule_actions_annotation in i.metadata.annotations:
            deployment = str(i.metadata.namespace + '/' + str(i.metadata.name))
            schedule_actions = parse_content(i.metadata.annotations[schedule_actions_annotation], deployment)
            scaling_dict[deployment] = schedule_actions

    if not scaling_dict:
        logging.info('No deployment is configured for schedule scaling')

    return scaling_dict

def hpa_for_scale():
    '''
    Getting the hpa configured for schedule scaling...
    '''

    v1 = client.AutoscalingV1Api()
    scaling_dict = {}

    hpas = v1.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)

    for i in hpas.items:
        if schedule_actions_annotation in i.metadata.annotations:
            hpa = str(i.metadata.namespace + '/' + str(i.metadata.name))
            schedule_actions = parse_content(i.metadata.annotations[schedule_actions_annotation], hpa)
            scaling_dict[hpa] = schedule_actions

    if not scaling_dict:
        logging.info('No hpa is configured for schedule scaling')

    return scaling_dict

def deployment_job_creator():
    """ Create CronJobs for configured Deployments """

    deployments__for_scale = deployments_for_scale()
    print("[INFO]",datetime.datetime.now(), "Deployments collected for scaling: ")
    for namespace_deployment, schedules in deployments__for_scale.items():
        namespace = namespace_deployment.split("/")[0]
        deployment = namespace_deployment.split("/")[1]
        for n in range(len(schedules)):
            schedules_n = schedules[n]
            replicas = schedules_n.get('replicas', None)
            schedule = schedules_n.get('schedule', None)
            print("[INFO]", datetime.datetime.now(), "Deployment: {}, Namespace: {}, Replicas: {}, Schedule: {}".format(deployment, namespace, replicas, schedule))

            with open("/root/schedule_scaling/templates/deployment-script.py", 'r') as script:
                script = script.read()
            deployment_script = script % {
                'namespace': namespace,
                'name': deployment,
                'replicas': int(replicas or -1),
                'time': EXECUTION_TIME,
            }
            i = 0
            while os.path.exists("/tmp/scaling_jobs/%s-%s.py" % (deployment, i)):
                i += 1
            script_creator = open("/tmp/scaling_jobs/%s-%s.py" % (deployment, i), "w")
            script_creator.write(deployment_script)
            script_creator.close()
            cmd = ['sleep 1 ; . /root/.profile ; /usr/bin/python', script_creator.name,
                   '2>&1 | tee -a', os.environ['SCALING_LOG_FILE']]
            cmd = ' '.join(map(str, cmd))
            scaling_cron = CronTab(user='root')
            job = scaling_cron.new(command=cmd)
            try:
                job.setall(schedule)
                job.set_comment("Scheduling_Jobs")
                scaling_cron.write()
            except Exception:
                print("[ERROR]", datetime.datetime.now(), 'Deployment: {} has syntax error in the schedule'.format(deployment))
                pass

def hpa_job_creator():
    """ Create CronJobs for configured hpa """

    hpa__for_scale = hpa_for_scale()
    print("[INFO]", datetime.datetime.now(), "HPA collected for scaling: ")
    for namespace_hpa, schedules in hpa__for_scale.items():
        namespace = namespace_hpa.split("/")[0]
        hpa = namespace_hpa.split("/")[1]
        for n in range(len(schedules)):
            schedules_n = schedules[n]
            minReplicas = schedules_n.get('minReplicas', None)
            maxReplicas = schedules_n.get('maxReplicas', None)
            schedule = schedules_n.get('schedule', None)
            print("[INFO]", datetime.datetime.now(), "HPA: {}, Namespace: {}, MinReplicas: {}, MaxReplicas: {}, Schedule: {}".format(hpa, namespace, minReplicas, maxReplicas, schedule))

            with open("/root/schedule_scaling/templates/hpa-script.py", 'r') as script:
                script = script.read()
            hpa_script = script % {
                'namespace': namespace,
                'name': hpa,
                'minReplicas': int(minReplicas or -1),
                'maxReplicas': int(maxReplicas or -1),
                'time': EXECUTION_TIME,
            }
            i = 0
            while os.path.exists("/tmp/scaling_jobs/%s-%s.py" % (hpa, i)):
                i += 1
            script_creator = open("/tmp/scaling_jobs/%s-%s.py" % (hpa, i), "w")
            script_creator.write(hpa_script)
            script_creator.close()
            cmd = ['sleep 1 ; . /root/.profile ; /usr/bin/python', script_creator.name,
                   '2>&1 | tee -a', os.environ['SCALING_LOG_FILE']]
            cmd = ' '.join(map(str, cmd))
            scaling_cron = CronTab(user='root')
            job = scaling_cron.new(command=cmd)
            try:
                job.setall(schedule)
                job.set_comment("Scheduling_Jobs")
                scaling_cron.write()
            except Exception:
                print("[ERROR]", datetime.datetime.now(),'HPA: {} has syntax error in the schedule'.format(hpa))
                pass

def parse_content(content, identifier):
    if content == None:
        return []

    if is_valid_url(content):
        schedules = fetch_schedule_actions_from_url(content)

        if schedules == None:
            return []

        return parse_schedules(schedules, identifier)

    return parse_schedules(content, identifier)

def is_valid_url(url):
    return re.search('^(https?)://(\\S+)\.(\\S{2,}?)(/\\S+)?$', url, re.I) != None

def fetch_schedule_actions_from_url(url):
    request = urllib.request.urlopen(url)
    try:
        content = request.read().decode('utf-8')
    except:
        content = None
    finally:
        request.close()

    return content

def parse_schedules(schedules, identifier):
    try:
        return json.loads(schedules)
    except Exception as err:
        print("[ERROR]", datetime.datetime.now(), '{} - Error in parsing JSON {} with error'.format(identifier, schedules), err)
        return []

if __name__ == '__main__':

    if os.getenv('KUBERNETES_SERVICE_HOST'):
        # ServiceAccountの権限で実行する
        config.load_incluster_config()
    else:
        # $HOME/.kube/config から読み込む
        config.load_kube_config()

    create_job_directory()
    clear_cron()
    deployment_job_creator()
    hpa_job_creator()
