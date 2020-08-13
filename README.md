# Kubernetes Schedule Scaler

This Application/ Kubernetes controller is used to schedule scale deployments in the cluster based in annotations.
The controller can work in conjunction with hpa. if hpa is configured the controller can adjust minReplicas and maxReplicas.
At the moment it supports reading the scaling definitions from directly in the annotations.

# Why fork?

- A less common resource(stackset) was targeted and we wanted to remove it.
- We wanted to remove the ability to save to S3 as well because it's hard to use.

## Usage


Just add the annotation to either your `Deployment`.

```
  annotations:
    zalando.org/schedule-actions: '[{"schedule": "10 18 * * *", "replicas": "3"}]'
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
        {"schedule": "30 4 * * 1,2,3,4,5", "minReplicas": "{{{HIGH_LOAD_REPLICAS}}}"},
        {"schedule": "00 8 * * 1,2,3,4,5", "minReplicas": "{{{REPLICAS}}}"},
        {"schedule": "00 21 * * 1,2,3,4,5", "minReplicas": "{{{MIN_REPLICAS}}}"},
        {"schedule": "30 5 * * 6,7", "minReplicas": "{{{HIGH_LOAD_REPLICAS}}}"},
        {"schedule": "00 9 * * 6,7", "minReplicas": "{{{REPLICAS}}}"},
        {"schedule": "00 21 * * 6,7", "minReplicas": "{{{MIN_REPLICAS}}}"}
      ]
```