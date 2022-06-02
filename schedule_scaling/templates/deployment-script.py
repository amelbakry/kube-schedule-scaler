from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time
import datetime
import random
import os

time.sleep(random.uniform(1, 10))

if os.getenv('KUBERNETES_SERVICE_HOST'):
    # ServiceAccountの権限で実行する
    config.load_incluster_config()
else:
    # $HOME/.kube/config から読み込む
    config.load_kube_config()

v1 = client.AppsV1Api()
replicas = %(replicas)d
body = {'spec': {'replicas': replicas}}

if replicas > -1:
    try:
      v1.patch_namespaced_deployment("%(name)s", "%(namespace)s", body)
      #api_response = v1.patch_namespaced_deployment("%(name)s", "%(namespace)s", body)
      #print(api_response)
    except ApiException as e:
      print("[ERROR]", datetime.datetime.now(),'deployment %(namespace)s/%(name)s has not been patched',e)

deployment = v1.read_namespaced_deployment("%(name)s","%(namespace)s")
if deployment.spec.replicas == replicas:
  print("[INFO]", datetime.datetime.now(), 'Deployment %(namespace)s/%(name)s has been scaled successfully to %(replicas)s replica at', %(time)s)
else:
  print("[ERROR]", datetime.datetime.now(), 'Something went wrong... deployment %(namespace)s/%(name)s has not been scaled to %(replicas)s')
