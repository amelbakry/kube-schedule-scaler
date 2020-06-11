from pykube import Deployment
import pykube

# extends pykube.Deployment, overriding version "extensions/v1beta1" with "apps/v1"
class Deployment(pykube.Deployment):

    version = "apps/v1"
