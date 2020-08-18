import pykube
import operator
import time
import datetime
import sys

def get_kube_api():
    try:
        config = pykube.KubeConfig.from_service_account()
    except FileNotFoundError:
        # local testing
        config = pykube.KubeConfig.from_file(os.path.expanduser('~/.kube/config'))
    api = pykube.HTTPClient(config)
    return api

api = get_kube_api()
hpa = pykube.HorizontalPodAutoscaler.objects(api).filter(namespace="%(namespace)s").get(name="%(name)s")

maxReplicas = %(maxReplicas)s
minReplicas = %(minReplicas)s

if hpa:
    if maxReplicas != None and minReplicas != None:
        hpa.obj["spec"]["maxReplicas"] = maxReplicas
        hpa.obj["spec"]["minReplicas"] = minReplicas
        hpa.update()

        if hpa.obj["spec"]["maxReplicas"] == maxReplicas and hpa.obj["spec"]["minReplicas"] == minReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
            print("[INFO]", datetime.datetime.now(), 'HPA %(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
        else:
            print("[ERROR] ", datetime.datetime.now(), ' Something went wrong... HPA %(name)s has not been scaled')

    elif minReplicas != None:
        currentMaxReplicas = hpa.obj["spec"].get('maxReplicas', {})

        if currentMaxReplicas:
            if currentMaxReplicas < minReplicas:
                print("[ERROR]", datetime.datetime.now(), 'You cannot set minReplicas(desired:{}) larger than maxReplicas(current:{}).'.format(minReplicas, currentMaxReplicas))
                sys.exit(1)

        hpa.obj["spec"]["minReplicas"] = minReplicas
        hpa.update()

        if hpa.obj["spec"]["minReplicas"] == minReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(name)s has been adjusted to minReplicas to %(minReplicas)s at', %(time)s)
        else:
            print("[INFO]", datetime.datetime.now(), 'Something went wrong... HPA %(name)s has not been scaled')

    elif maxReplicas != None:
        currentMinReplicas = hpa.obj["spec"].get('minReplicas', {})

        if currentMinReplicas:
            if currentMinReplicas > maxReplicas:
                print("[ERROR]", datetime.datetime.now(), 'You cannot set maxReplicas(desired:{}) larger than minReplicas(current:{}).'.format(maxReplicas, currentMinReplicas))
                sys.exit(1)

        hpa.obj["spec"]["maxReplicas"] = maxReplicas
        hpa.update()

        if hpa.obj["spec"]["maxReplicas"] == maxReplicas:
            print("[INFO]", datetime.datetime.now(), 'HPA %(name)s has been adjusted to maxReplicas to %(maxReplicas)s at', %(time)s)
        else:
            print("[INFO]", datetime.datetime.now(), 'Something went wrong... HPA %(name)s has not been scaled')
