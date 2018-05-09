FROM centos:7

VOLUME /payload

RUN yum update -y && \
    yum install python-virtualenv make -y

WORKDIR /payload
ENTRYPOINT virtualenv testenv && \
    source testenv/bin/activate  && \
    pip install -U setuptools && \
    pip install -U funcsigs && \
    pip install -U -r requirements-tests.txt && \
    pip install -U . && \
    py.test
