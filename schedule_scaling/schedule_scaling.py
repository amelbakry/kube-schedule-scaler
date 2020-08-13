""" Collecting Deployments configured for Scaling """
import os
import pathlib
import json
import logging
import shutil
import pykube
import re
import urllib.request
from crontab import CronTab

EXECUTION_TIME = 'datetime.datetime.now().strftime("%d-%m-%Y %H:%M UTC")'


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


def get_kube_api():
    """ Initiating the API from Service Account or when running locally from ~/.kube/config """
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api


def deployments_for_scale():
    '''
    Getting the deployments configured for schedule scaling...
    '''
    api = get_kube_api()
    deployments = []
    scaling_dict = {}
    for namespace in list(pykube.Namespace.objects(api)):
        namespace = str(namespace)
        for deployment in pykube.Deployment.objects(api).filter(namespace=namespace):
            annotations = deployment.metadata.get('annotations', {})
            f_deployment = str(namespace + '/' + str(deployment))

            schedule_actions = parse_content(annotations.get('zalando.org/schedule-actions', None), f_deployment)

            if schedule_actions is None or len(schedule_actions) == 0:
                continue

            deployments.append([deployment.metadata['name']])
            scaling_dict[f_deployment] = schedule_actions
    if not deployments:
        logging.info('No deployment is configured for schedule scaling')

    return scaling_dict

def hpa_job_creator():
    """ Create CronJobs for configured hpa """

    hpa__for_scale = hpa_for_scale()
    print("HPA collected for scaling: ")
    for namespace_hpa, schedules in hpa__for_scale.items():
        namespace = namespace_hpa.split("/")[0]
        hpa = namespace_hpa.split("/")[1]
        for n in range(len(schedules)):
            schedules_n = schedules[n]
            minReplicas = schedules_n.get('minReplicas', None)
            maxReplicas = schedules_n.get('maxReplicas', None)
            schedule = schedules_n.get('schedule', None)
            print("HPA: %s, Namespace: %s, MinReplicas: %s, MaxReplicas: %s, Schedule: %s"
                  % (hpa, namespace, minReplicas, maxReplicas, schedule))

            with open("/root/schedule_scaling/templates/hpa-script.py", 'r') as script:
                script = script.read()
            hpa_script = script % {
                'namespace': namespace,
                'name': hpa,
                'minReplicas': minReplicas,
                'maxReplicas': maxReplicas,
                'time': EXECUTION_TIME,
            }
            i = 0
            while os.path.exists("/tmp/scaling_jobs/%s-%s.py" % (hpa, i)):
                i += 1
            script_creator = open("/tmp/scaling_jobs/%s-%s.py" % (hpa, i), "w")
            script_creator.write(hpa_script)
            script_creator.close()
            cmd = ['sleep 50 ; . /root/.profile ; /usr/bin/python', script_creator.name,
                   '2>&1 | tee -a', os.environ['SCALING_ACTIVITIES_LOG']]
            cmd = ' '.join(map(str, cmd))
            scaling_cron = CronTab(user='root')
            job = scaling_cron.new(command=cmd)
            try:
                job.setall(schedule)
                job.set_comment("Scheduling_Jobs")
                scaling_cron.write()
            except Exception:
                print('HPA: %s has syntax error in the schedule' % (hpa))
                pass

def hpa_for_scale():
    '''
    Getting the hpa configured for schedule scaling...
    '''
    api = get_kube_api()
    hpas = []
    scaling_dict = {}
    for namespace in list(pykube.Namespace.objects(api)):
        namespace = str(namespace)
        for hpa in pykube.HorizontalPodAutoscaler.objects(api).filter(namespace=namespace):
            annotations = hpa.metadata.get('annotations', {})
            f_hpa = str(namespace + '/' + str(hpa))

            schedule_actions = parse_content(annotations.get('zalando.org/schedule-actions', None), f_hpa)

            if schedule_actions is None or len(schedule_actions) == 0:
                continue

            hpas.append([hpa.metadata['name']])
            scaling_dict[f_hpa] = schedule_actions
    if not hpas:
        logging.info('No hpa is configured for schedule scaling')

    return scaling_dict

def deployment_job_creator():
    """ Create CronJobs for configured Deployments """

    deployments__for_scale = deployments_for_scale()
    print("Deployments collected for scaling: ")
    for deployment_namespace, schedules in deployments__for_scale.items():
        namespace = namespace_deployment.split("/")[0]
        deployment = namespace_deployment.split("/")[1]
        for n in range(len(schedules)):
            schedules_n = schedules[n]
            replicas = schedules_n.get('replicas', None)
            schedule = schedules_n.get('schedule', None)
            print("Deployment: %s, Namespace: %s, Replicas: %s, Schedule: %s"
                  % (deployment, namespace, replicas, schedule))

            with open("/root/schedule_scaling/templates/deployment-script.py", 'r') as script:
                script = script.read()
            deployment_script = script % {
                'namespace': namespace,
                'name': deployment,
                'replicas': replicas,
                'time': EXECUTION_TIME,
            }
            i = 0
            while os.path.exists("/tmp/scaling_jobs/%s-%s.py" % (deployment, i)):
                i += 1
            script_creator = open("/tmp/scaling_jobs/%s-%s.py" % (deployment, i), "w")
            script_creator.write(deployment_script)
            script_creator.close()
            cmd = ['sleep 50 ; . /root/.profile ; /usr/bin/python', script_creator.name,
                   '2>&1 | tee -a', os.environ['SCALING_ACTIVITIES_LOG']]
            cmd = ' '.join(map(str, cmd))
            scaling_cron = CronTab(user='root')
            job = scaling_cron.new(command=cmd)
            try:
                job.setall(schedule)
                job.set_comment("Scheduling_Jobs")
                scaling_cron.write()
            except Exception:
                print('Deployment: %s has syntax error in the schedule' % (deployment))
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
        print('%s - Error in parsing JSON %s with error' % (identifier, schedules), err)
        return []

if __name__ == '__main__':
    create_job_directory()
    clear_cron()
    deployment_job_creator()
    hpa_job_creator()
