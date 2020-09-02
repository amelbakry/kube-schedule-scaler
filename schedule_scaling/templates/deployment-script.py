import pykube
import operator
import time
import datetime

def get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api


api = get_kube_api()
deployment = pykube.Deployment.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")

replicas = %(replicas)s

if replicas != None:
    deployment.replicas = replicas
    try:
      deployment.update()
    except Exception as err:
      print("[ERROR]", datetime.datetime.now(),'deployment %(name)s has not been updated',err)

    deployment = pykube.Deployment.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")
    if deployment.replicas == replicas:
        print("[INFO]", datetime.datetime.now(), 'Deployment %(name)s has been scaled successfully to %(replicas)s replica at', %(time)s)
    else:
        print("[ERROR]", datetime.datetime.now(), 'Something went wrong... deployment %(name)s has not been scaled')
