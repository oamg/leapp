FROM fedora:26

ENV GIT_BRANCH          master
ENV GIT_URL             https://github.com/leapp-to/ansible-devel-env.git
ENV GIT_CLONE_DIR       ansible-devel-env
ENV HOME                /root
ENV LEAPP_HOME          $HOME/leapp

VOLUME ["${LEAPP_HOME}"]

RUN echo "echo \"Welcome to Leapp development image. The development environment is prepared for you in ${LEAPP_HOME}\"" >> $HOME/.bashrc && \
    echo "echo -e \"\n\$(ls -l ${LEAPP_HOME})\n\"" >> $HOME/.bashrc && \
    echo "export SHELL=/bin/bash" >> $HOME/.bashrc

RUN dnf upgrade -y && \
    dnf -y install \
    ansible \
    'dnf-command(copr)' \
    docker \
    git \
    passwd \
    && dnf -y clean all

RUN echo "leapp" | passwd root --stdin

RUN systemctl enable docker

## Run the Ansible playbook before the container starts. This way the git data are
## not distributed in the image and will be updated each time the container
## is created.
CMD /bin/bash -c " \
    cd ${HOME} && \
    git clone ${GIT_URL} ${GIT_CLONE_DIR} 2>&1 | tee ${HOME}/leapp-setup.log && \
    cd ${GIT_CLONE_DIR} && \
    git checkout ${GIT_BRANCH} 2>&1 | tee -a ${HOME}/leapp-setup.log && \
    [ ! -e ${LEAPP_HOME}/.installed ] && \
    ansible-playbook ansible/leapp_dev.yml 2>&1 | tee -a ${HOME}/leapp-setup.log && \
    touch ${LEAPP_HOME}/.installed; \
    exec /sbin/init \
"
