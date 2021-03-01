import pykube
import operator
import time
import datetime
import sys
import random

def get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api

time.sleep(random.uniform(1, 10))
api = get_kube_api()
hpa = pykube.HorizontalPodAutoscaler.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")

maxReplicas = %(maxReplicas)s
minReplicas = %(minReplicas)s

if hpa:
    if maxReplicas != None and minReplicas != None:
        hpa.obj["spec"]["maxReplicas"] = maxReplicas
        hpa.obj["spec"]["minReplicas"] = minReplicas

        try:
          hpa.update()
        except Exception as err:
          print("[ERROR]", datetime.datetime.now(),'HPA %(namespace)s/%(name)s has not been updated',err)

        hpa = pykube.HorizontalPodAutoscaler.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")
        if hpa.obj["spec"]["maxReplicas"] == maxReplicas and hpa.obj["spec"]["minReplicas"] == minReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
            print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
        else:
            print("[ERROR]", datetime.datetime.now(), ' Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(maxReplicas to %(maxReplicas)s, minReplicas to %(minReplicas)s)')

    elif minReplicas != None:
        currentMaxReplicas = hpa.obj["spec"].get('maxReplicas', {})

        if currentMaxReplicas:
            if currentMaxReplicas < minReplicas:
                print("[ERROR]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s cannot be set minReplicas(desired:{}) larger than maxReplicas(current:{}).'.format(minReplicas, currentMaxReplicas))
                sys.exit(1)

        hpa.obj["spec"]["minReplicas"] = minReplicas

        try:
          hpa.update()
        except Exception as err:
          print("[ERROR]", datetime.datetime.now(),'HPA %(namespace)s/%(name)s has not been updated',err)

        hpa = pykube.HorizontalPodAutoscaler.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")
        if hpa.obj["spec"]["minReplicas"] == minReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
        else:
            print("[ERROR]", datetime.datetime.now(), 'Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(minReplicas to %(minReplicas)s)')

    elif maxReplicas != None:
        currentMinReplicas = hpa.obj["spec"].get('minReplicas', {})

        if currentMinReplicas:
            if currentMinReplicas > maxReplicas:
                print("[ERROR]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s cannot be set maxReplicas(desired:{}) larger than minReplicas(current:{}).'.format(maxReplicas, currentMinReplicas))
                sys.exit(1)

        hpa.obj["spec"]["maxReplicas"] = maxReplicas

        try:
          hpa.update()
        except Exception as err:
          print("[ERROR]", datetime.datetime.now(),'HPA %(namespace)s/%(name)s has not been updated',err)

        hpa = pykube.HorizontalPodAutoscaler.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")
        if hpa.obj["spec"]["maxReplicas"] == maxReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(namespace)s/%(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
        else:
            print("[ERROR]", datetime.datetime.now(), 'Something went wrong... HPA %(namespace)s/%(name)s has not been scaled(maxReplicas to %(maxReplicas)s)')
