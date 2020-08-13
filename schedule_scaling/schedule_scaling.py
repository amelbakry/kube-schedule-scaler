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


def deployments_to_scale():
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

            with open("/root/schedule_scaling/templates/deployment-script.py", 'r') as script:
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
    deploy_job_creator()
