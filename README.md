# Kubernetes Schedule Scaler

Kubernetes Schedule Scaler allows you to change the number of running replicas
of a Deployment at specific times. A common use case is to turn down applications
that don't need to be available 24/7 to reduce cluster resource utilization.

## Usage

Just add the annotation to either your `Deployment`.

```
  annotations:
    zalando.org/schedule-actions: '[{"schedule": "10 18 * * *", "replicas": "3"}]'
```
The following fields are available
* `schedule` - Typical crontab format
* `replicas` - the number of replicas to scale to
* `minReplicas` - in combination with an `hpa` will adjust the `minReplicas` else be ignored
* `maxReplicas` - in combination with an `hpa` will adjust the `maxReplicas` else be ignored

### Deployment Example

```bash
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    application: nginx-deployment
  annotations:
    zalando.org/schedule-actions: |
      [
        {"schedule": "30 4 * * 1,2,3,4,5", "minReplicas": "{{{HIGH_LOAD_REPLICAS}}}"},
        {"schedule": "00 8 * * 1,2,3,4,5", "minReplicas": "{{{REPLICAS}}}"},
        {"schedule": "00 21 * * 1,2,3,4,5", "minReplicas": "{{{MIN_REPLICAS}}}"},
        {"schedule": "30 5 * * 6,7", "minReplicas": "{{{HIGH_LOAD_REPLICAS}}}"},
        {"schedule": "00 9 * * 6,7", "minReplicas": "{{{REPLICAS}}}"},
        {"schedule": "00 21 * * 6,7", "minReplicas": "{{{MIN_REPLICAS}}}"}
      ]
```

## Debugging

If your scaling action has not been executed for some reason, you can check with the below steps:

```bash
kubectl get pod | grep kube-schedule
kube-schedule-scaler-75644b8f79-h59s2                    1/1       Running                 0          3d
```
Check the logs for your specific deployment/stack
```bash
kubectl logs kube-schedule-scaler-75644b8f79-h59s2 | grep scale | grep node-live
Stack pegasus-node-live has been scaled successfully to 40 minReplicas at 11-03-2019 21:00 UTC
Stack pegasus-node-live has been scaled successfully to 120 minReplicas at 12-03-2019 05:30 UTC
Stack pegasus-node-live has been scaled successfully to 80 minReplicas at 12-03-2019 07:00 UTC
Stack pegasus-node-live has been scaled successfully to 40 minReplicas at 12-03-2019 21:00 UTC
Stack pegasus-node-live has been scaled successfully to 120 minReplicas at 13-03-2019 05:30 UTC
Stack pegasus-node-live has been scaled successfully to 80 minReplicas at 13-03-2019 07:00 UTC
Stack pegasus-node-live has been scaled successfully to 40 minReplicas at 13-03-2019 21:00 UTC
Stack pegasus-node-live has been scaled successfully to 120 minReplicas at 14-03-2019 05:30 UTC
Stack pegasus-node-live has been scaled successfully to 80 minReplicas at 14-03-2019 07:00 UTC
Stack pegasus-node-live has been scaled successfully to 40 minReplicas at 14-03-2019 21:00 UTC
Stack pegasus-node-live has been scaled successfully to 120 minReplicas at 15-03-2019 05:30 UTC
Stack pegasus-node-live has been scaled successfully to 80 minReplicas at 15-03-2019 07:00 UTC
```

![Pods](image/pods.png)

Check for specific deployment at specific time
```bash
kubectl logs kube-schedule-scaler-87f9649f5-btnt7 | grep nginx-deployment-2 | grep "28-12-2018 09:50"
Deployment nginx-deployment-2 has been scaled successfully to 4 replica at 28-12-2018 09:50 UTC
```
