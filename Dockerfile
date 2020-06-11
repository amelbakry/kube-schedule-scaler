From ubuntu:16.04
MAINTAINER "eng.ahmed.elbakry@gmail.com"

# Install python tools and dev packages
RUN apt-get update \
    && apt-get install -q -y --no-install-recommends  python3-pip python3-setuptools python3-wheel gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# set python 3 as the default python version
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
RUN pip3 install --upgrade pip requests setuptools pipenv
RUN pip3 install pykube
RUN pip3 install python-crontab
RUN pip3 install croniter
RUN pip3 install boto3
RUN apt-get update &&  apt-get install -y apt-transport-https curl gnupg sudo \
    && curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
RUN sudo touch /etc/apt/sources.list.d/kubernetes.list \
    && echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
RUN sudo apt-get update \
    && sudo apt-get install -y kubectl cron

ADD schedule_scaling /root/schedule_scaling
COPY ./run_missed_jobs.py /root
RUN chmod a+x /root/run_missed_jobs.py

COPY ./startup.sh /root
RUN chmod a+x /root/startup.sh
CMD /root/startup.sh

ENV PYTHONPATH "${PYTHONPATH}:/root/schedule_scaling"
