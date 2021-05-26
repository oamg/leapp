FROM registry.centos.org/centos:7

VOLUME /payload

RUN yum update -y && \
    yum install python-virtualenv make -y && \
    yum -y install epel-release && \
    yum -y install python-pip python3-pip && \
    python2 -m pip install --upgrade pip==20.3.4 && \
    python3 -m pip install --upgrade pip==20.3.4

WORKDIR /payload
ENTRYPOINT virtualenv testenv && \
    source testenv/bin/activate  && \
    pip install -U setuptools && \
    pip install -U funcsigs && \
    pip install -U -r requirements-tests.txt && \
    pip install -U . && \
    py.test tests/scripts
