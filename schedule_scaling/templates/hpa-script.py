from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time
import datetime
import sys
import random
import os

time.sleep(random.uniform(1, 10))

if os.getenv('KUBERNETES_SERVICE_HOST'):
    # ServiceAccountの権限で実行する
    config.load_incluster_config()
else:
    # $HOME/.kube/config から読み込む
    config.load_kube_config()

v1 = client.AutoscalingV1Api()

maxReplicas = %(maxReplicas)d
minReplicas = %(minReplicas)d

def patch_hpa(body):
    try:
        v1.patch_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s", body)
        #api_response = v1.patch_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s", body)
        #print(api_response)
    except ApiException as err:
        print("[ERROR]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has not been updated', err)

if maxReplicas > 0 and minReplicas > 0:
    body = {"spec": {"minReplicas": minReplicas, "maxReplicas": maxReplicas}}

    patch_hpa(body)
    hpa = v1.read_namespaced_horizontal_pod_autoscaler("%(name)s","%(namespace)s")
    if hpa.spec.max_replicas == maxReplicas and hpa.spec.min_replicas == minReplicas:
        print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
        print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
    else:
        print("[ERROR]", datetime.datetime.now(), ' Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(maxReplicas to %(maxReplicas)s, minReplicas to %(minReplicas)s)')

elif maxReplicas == 0 or minReplicas == 0:
    print("[ERROR]", datetime.datetime.now(),
          'Neither maxReplicas nor minReplicas can be set to 0. HPA %(namespace)s/%(name)s has not been scaled')
    sys.exit(1)

elif minReplicas > 0:
    current_hpa = v1.read_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s")
    currentMaxReplicas = current_hpa.spec.max_replicas

    if currentMaxReplicas:
        if currentMaxReplicas < minReplicas:
            print("[ERROR]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s cannot be set minReplicas(desired:{}) larger than maxReplicas(current:{}).'.format(minReplicas, currentMaxReplicas))
            sys.exit(1)

    body = {"spec": {"minReplicas": minReplicas}}

    patch_hpa(body)

    hpa = v1.read_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s")
    if hpa.spec.min_replicas == minReplicas:
        print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
    else:
        print("[ERROR]", datetime.datetime.now(), 'Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(minReplicas to %(minReplicas)s)')

elif maxReplicas > 0:
    current_hpa = v1.read_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s")
    currentMinReplicas = current_hpa.spec.min_replicas

    if currentMinReplicas:
        if currentMinReplicas > maxReplicas:
            print("[ERROR]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s cannot be set maxReplicas(desired:{}) larger than minReplicas(current:{}).'.format(maxReplicas, currentMinReplicas))
            sys.exit(1)

    body = {"spec": {"maxReplicas": maxReplicas}}
    patch_hpa(body)

    hpa = v1.read_namespaced_horizontal_pod_autoscaler("%(name)s", "%(namespace)s")
    if hpa.spec.max_replicas == maxReplicas:
        print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
    else:
        print("[ERROR]", datetime.datetime.now(), 'Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(maxReplicas to %(maxReplicas)s)')
