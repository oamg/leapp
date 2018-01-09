FROM fedora:26

ENV BUILD_SCRIPT        build_leapp_environment.sh
ENV BUILD_SCRIPT_URL    https://leapp-to.github.io/files/$BUILD_SCRIPT
ENV HOME                /root
ENV LEAPP_HOME          $HOME/leapp


RUN dnf update -y && \
    dnf -y install 'dnf-command(copr)' sudo libvirt docker passwd && \
    dnf -y clean all

RUN systemctl enable libvirtd docker

RUN echo "echo \"Welcome in leapp development image. The development environment is prepared for you in /root/leapp\"" >> $HOME/.bashrc && \
    echo "echo -e \"\n\$(ls -l ${LEAPP_HOME})\n\"" >> $HOME/.bashrc && \
    echo "export SHELL=/bin/bash" >> $HOME/.bashrc

VOLUME ["${LEAPP_HOME}", "/lib/libvirt"]

RUN echo "leapp" | passwd root --stdin

## Run the build script before the container starts. This way the git data are
## not distributed in the image and will be updated each time the container
## is created.
CMD /bin/bash -c " \
    cd ${HOME} && \
    curl -O ${BUILD_SCRIPT_URL} && \
        [ ! -e ${LEAPP_HOME}/.installed ] && \
        $SHELL ${BUILD_SCRIPT} 2>&1 | tee ${HOME}/leapp-setup.log && \
        touch ${LEAPP_HOME}/.installed; \
    M=$(ls -1 /dev/loop* | grep -v loop-control | sort -r | head -n 1 | sed -e 's/\/dev\/loop//'); \
    mknod -m660 $(echo /dev/loop$((M+1))) b 7 $((M+1)); \
    mknod -m660 $(echo /dev/loop$((M+2))) b 7 $((M+2)); \
    exec /sbin/init \
"
