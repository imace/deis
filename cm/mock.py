
from __future__ import unicode_literals

from celery import task

from api.models import Formation, App


@task
def configure(config, node, layer):
    config['config'] = config
    config['node_id'] = node.id
    config['layer_id'] = layer.id
    return config


@task
def update(obj):
    return


@task
def destroy(obj):
    return


@task
def converge(instance=None):
    if instance.__class__ == Formation:
        print('Converging Formation...')
    elif instance.__class__ == App:
        print('Converging Application')
    elif instance is None:
        print('Converging Controller')
    return
