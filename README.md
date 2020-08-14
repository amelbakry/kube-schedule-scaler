# Kubernetes Schedule Scaler

This Application/ Kubernetes controller is used to schedule scale deployments in the cluster based in annotations.
The controller can work in conjunction with hpa. if hpa is configured the controller can adjust minReplicas and maxReplicas.
At the moment it supports reading the scaling definitions from directly in the annotations.

# Why fork?

- A less common resource(stackset) was targeted and we wanted to remove it.
- We wanted to remove the ability to save to S3 as well because it's hard to use.

## Usage

### deployment

Add the annotation to either your `Deployment`.

```
  annotations:
    zalando.org/schedule-actions: '[{"schedule": "10 18 * * *", "replicas": "3"}]'
```

### HPA

```
  annotations:
    zalando.org/schedule-actions: '[{"schedule": "10 18 * * *", "minReplicas": "3"}]'
```

## Available Fields 

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
        {"schedule": "30 4 * * 1,2,3,4,5", "replicas": "{{{HIGH_LOAD_REPLICAS}}}"},
        {"schedule": "00 8 * * 1,2,3,4,5", "replicas": "{{{REPLICAS}}}"}
      ]
```

### HPA Example

```bash
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  annotations:
    zalando.org/schedule-actions: |
      [
        {"schedule": "15 4 * * *", "minReplicas": "1"},
        {"schedule": "12 4 * * *", "maxReplicas": "20"},
        {"schedule": "10 4 * * *", "maxReplicas": "15", "minReplicas": "2"}
      ]
  name: php-apache
spec:
  maxReplicas: 20
  minReplicas: 1
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  targetCPUUtilizationPercentage: 50
```

autoscaling/v2beta2

```bash
apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
  annotations:
    zalando.org/schedule-actions: |
      [
        {"schedule": "20 7 * * *", "maxReplicas": "15", "minReplicas": "2"}
      ]
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 7
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```
  
