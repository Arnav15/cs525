from fabric.api import *

s = 'sp18-cs525-g05-{:02d}.cs.illinois.edu'

env.hosts = [s.format(x) for x in range(1, 15+1)]

def git_clone():
    sudo('mkdir -p /opt')
    with cd('/opt'):
        sudo('git clone https://github.com/Arnav15/cs525.git blockchain')

def git_checkout(branch='master'):
    with cd('/opt/blockchain'):
        sudo('git checkout {}'.format(branch))

def git_pull():
    with cd('/opt/blockchain'):
        sudo('git pull')

def install_py36():
    sudo('yum -y install https://centos7.iuscommunity.org/ius-release.rpm')
    sudo('yum -y install python36u python36u-pip')

def install_cryptography():
    sudo('yum install -y redhat-rpm-config gcc libffi-devel openssl-dev')
    sudo('pip3.6 install cryptography')

def own_opt():
    with cd('/opt'):
        sudo('chown :csvm525-stu blockchain')
        sudo('chmod g+w blockchain')
