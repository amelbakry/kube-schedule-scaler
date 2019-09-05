import time
import datetime
import os
import operator
import pykube
import sys
sys.path.insert(0, '/root/schedule_scaling/resources')
from Stackset import StackSet



def get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api


api = get_kube_api()
stack = StackSet.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")

replicas = %(replicas)s
minReplicas = %(minReplicas)s
maxReplicas = %(maxReplicas)s

if replicas != None:
    stack.set_replicas(replicas)

if minReplicas != None and stack.has_hpa():
    stack.set_min_replicas(minReplicas)

if maxReplicas != None and stack.has_hpa():
    stack.set_max_replicas(maxReplicas)

stack.update()
time.sleep(1)

ok = False

if replicas != None and stack.get_replicas() == replicas:
    print('Stack %(name)s has been scaled successfully to %(replicas)s replica at', %(time)s)
    ok = True

if minReplicas != None and stack.get_min_replicas() == minReplicas:
    print('Stack %(name)s has been scaled successfully to %(minReplicas)s minReplicas at', %(time)s)
    ok = True

if maxReplicas != None and stack.get_max_replicas() == maxReplicas:
    print('Stack %(name)s has been scaled successfully to %(maxReplicas)s maxReplicas at', %(time)s)
    ok = True

if not ok:
    print('Something went wrong... Stack %(name)s has not been scaled')

