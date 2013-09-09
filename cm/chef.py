
from __future__ import unicode_literals

import os.path
import re
import subprocess

from celery.canvas import group
from celery import task

from api.models import Formation
from provider import util
import time
from cm.chef_api import ChefAPI
import json


CHEF_CONFIG_PATH = '/etc/chef'
CHEF_INSTALL_TYPE = 'gems'
CHEF_RUBY_VERSION = '1.9.1'
CHEF_ENVIRONMENT = '_default'


# load chef config using CHEF_CONFIG_PATH
try:
    # parse controller's chef config for server_url and client_name
    _client_cfg_path = os.path.join(CHEF_CONFIG_PATH, 'client.rb')
    if not os.path.exists(_client_cfg_path):
        raise EnvironmentError('Could not find {}'.format(_client_cfg_path))
    with open(_client_cfg_path) as f:
        _data = f.read()
    # construct a dict from the ruby client.rb
    _d = {}
    for m in re.findall(r'''^([a-zA-Z0-9_]+)[ \t]+(.*)$''',
                        _data, re.MULTILINE):
        _d[m[0]] = m[1].strip("'").strip('"')
    # set global variables from client.rb
    CHEF_SERVER_URL = _d['chef_server_url']
    CHEF_NODE_NAME = _d['node_name']
    CHEF_CLIENT_NAME = _d['node_name']
    CHEF_VALIDATION_NAME = _d['validation_client_name']
    # read the client key
    _client_pem_path = os.path.join(CHEF_CONFIG_PATH, 'client.pem')
    CHEF_CLIENT_KEY = subprocess.check_output(
        ['sudo', '/bin/cat', _client_pem_path]).strip('\n')
    # read the validation key
    _valid_pem_path = os.path.join(CHEF_CONFIG_PATH, 'validation.pem')
    CHEF_VALIDATION_KEY = subprocess.check_output(
        ['sudo', '/bin/cat', _valid_pem_path]).strip('\n')
except Exception as e:
    print 'Error: failed to auto-configure Chef -- {}'.format(e)


@task
def update(instance):
    return


@task
def destroy(instance):
#     # purge the node & client records from chef server
#     client = ChefAPI(CHEF_SERVER_URL,
#                      CHEF_CLIENT_NAME,
#                      CHEF_CLIENT_KEY)
#     client.delete_node(instance.id)
#     client.delete_client(instance.id)
    return


def update_user(user):
    client = ChefAPI(CHEF_SERVER_URL,
                     CHEF_CLIENT_NAME,
                     CHEF_CLIENT_KEY)
    # client.create_databag_item('deis-users', user.username, user.calculate())
    client.update_databag_item('deis-users', user.username, user.calculate())


def update_app(app):
    client = ChefAPI(CHEF_SERVER_URL,
                     CHEF_CLIENT_NAME,
                     CHEF_CLIENT_KEY)
    client.update_databag_item('deis-apps', app.id, app.calculate())


def update_formation(formation, client):
    client.update_databag_item('deis-formations', formation.id, formation.calculate())


@task
def converge(instance=None):
    return


def converge_controller():
    # NOTE: converging the controller can overwrite any in-place
    # changes to application code
    return subprocess.check_output(
        ['sudo', 'chef-client', '--override-runlist', 'recipe[deis::gitosis]'])


def converge_node(node_id, ssh_username, fqdn, ssh_private_key,
                  command='sudo chef-client'):
    ssh = util.connect_ssh(ssh_username, fqdn, 22, ssh_private_key)
    output, rc = ssh.exec_ssh(ssh, command)
    return output, rc


def converge_formation(formation_id):
    formation = Formation.objects.get(id=formation_id)
    nodes = formation.node_set.all()
    subtasks = []
    for n in nodes:
        subtask = converge_node.s(n.id,
                                  n.layer.flavor.ssh_username,
                                  n.fqdn,
                                  n.layer.flavor.ssh_private_key)
        subtasks.append(subtask)
    job = group(*subtasks)
    return job.apply_async().join()


@task
def bootstrap_node(node):
    # loop until node is registered with chef
    # if chef bootstrapping fails, the node will not complete registration
    registered = False
    while not registered:
        # reinstatiate the client on each poll attempt
        # to avoid disconnect errors
        client = ChefAPI(CHEF_SERVER_URL,
                         CHEF_CLIENT_NAME,
                         CHEF_CLIENT_KEY)
        resp, status = client.get_node(node.id)
        if status == 200:
            body = json.loads(resp)
            # wait until idletime is not null
            # meaning the node is registered
            if body.get('automatic', {}).get('idletime'):
                break
        time.sleep(5)


@task(name='chef.configure')
def configure(config, node, layer):
    # http://cloudinit.readthedocs.org/en/latest/topics/examples.html#install-and-run-chef-recipes
    config = config['chef'] = {}
    config['node_name'] = node.id
    # get run_list, attributes and chef version from the layer
    run_list = layer.config.get('run_list')
    if run_list:
        config['run_list'] = run_list.split(',')
    attrs = layer.config.get('initial_attributes')
    if attrs:
        config['initial_attributes'] = attrs
    chef_version = layer.config.get('chef_version')
    if chef_version:
        config['version'] = chef_version
    # add global chef config
    config['ruby_version'] = CHEF_RUBY_VERSION
    config['server_url'] = CHEF_SERVER_URL
    config['install_type'] = CHEF_INSTALL_TYPE
    config['environment'] = CHEF_ENVIRONMENT
    config['validation_name'] = CHEF_VALIDATION_NAME
    config['validation_key'] = CHEF_VALIDATION_KEY
    return config
