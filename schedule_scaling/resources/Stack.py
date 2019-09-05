import abc
from pykube.objects import NamespacedAPIObject

class Scalable(abc.ABC):

    @abc.abstractmethod
    def set_replicas(self, count: int):
        pass

    @abc.abstractmethod
    def get_replicas(self):
        pass

class Stack(NamespacedAPIObject, Scalable):
    """
    Use latest workloads API version (apps/v1), pykube is stuck with old version
    """

    version = "zalando.org/v1"
    endpoint = "stacks"
    kind = "Stack"

    def set_replicas(self, count):
        self.obj['spec']['replicas'] = count

    def get_replicas(self):
        return int(self.obj['spec']['replicas'])

    def has_hpa(self):
        return 'horizontalPodAutoscaler' in self.obj['spec']

    def get_min_replicas(self):
        return self.obj['spec']['horizontalPodAutoscaler']['minReplicas']

    def set_min_replicas(self, min_replicas):
        self.obj['spec']['horizontalPodAutoscaler']['minReplicas'] = min_replicas

    def get_max_replicas(self):
        return self.obj['spec']['horizontalPodAutoscaler']['maxReplicas']

    def set_max_replicas(self, max_replicas):
        self.obj['spec']['horizontalPodAutoscaler']['maxReplicas'] = max_replicas

    def save_state(self):
        self.annotations[DOWNSCALER_SAVED_ANNOTATION] = json.dumps(
            self.obj['spec']['horizontalPodAutoscaler'])
        self.obj['spec']['horizontalPodAutoscaler'] = None
