FROM fedora:26

ENV BUILD_SCRIPT        build_leapp_environment.sh
ENV BUILD_SCRIPT_URL    https://leapp-to.github.io/files/$BUILD_SCRIPT
ENV HOME                /root
ENV LEAPP_HOME          $HOME/leapp


RUN dnf update -y && \
    dnf -y install 'dnf-command(copr)' sudo libvirt docker && \
    dnf -y clean all

RUN systemctl enable libvirtd docker

RUN echo "echo \"Welcome in leapp development image. The development environment is prepared for you in /root/leapp\"" >> $HOME/.bashrc && \
    echo "echo -e \"\n\$(ls -l ${LEAPP_HOME})\n\"" >> $HOME/.bashrc && \
    echo "export SHELL=/bin/bash" >> $HOME/.bashrc


VOLUME ["${LEAPP_HOME}", "/lib/libvirt"]

## Run the build script before the container starts. This way the git data are
## not distributed in the image and will be updated each time the container
## is created.
CMD /bin/bash -c " \
    cd ${HOME} && \
    curl -O ${BUILD_SCRIPT_URL} && \
        [ ! -e ${LEAPP_HOME}/.installed ] && \
        $SHELL ${BUILD_SCRIPT} 2>&1 | tee ${HOME}/leapp-setup.log && \
        touch ${LEAPP_HOME}/.installed; \
    libvirtd -d && virtlockd -d && virtlogd -d; \
    exec $SHELL \
"
