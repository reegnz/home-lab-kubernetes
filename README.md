# Homelab for kubernetes

## Getting started

Have the following dependencies installed and configured:

- [kustomize](https://kustomize.io)
- [helm](https://helm.sh/)
- [pre-commit](https://pre-commit.com/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
- [direnv](https://direnv.net/)
- [gojq](https://github.com/itchyny/gojq)

## Howto

Put kustomize base layers into the `dry/applications/{app}/base` directory.
Put environment specific overlays into the `dry/applications/{app}/env/{env}` directories.

To hydrate the yaml manifests for deployment, run the `pre-commit run hydrate-kustomize` script.

Environment specific direnv config can be put into the `dry/envs/{env}` directory.
It will be synced to the wet app directories when running the hydration script.
