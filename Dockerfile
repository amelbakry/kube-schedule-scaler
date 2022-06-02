FROM ubuntu:22.04
MAINTAINER "sakamoto@chatwork.com"

# Install python tools and dev packages
RUN apt-get update \
    && apt-get install -q -y --no-install-recommends  python3-pip python3-setuptools python3-wheel gcc cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# set python 3 as the default python version
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
RUN pip3 install --upgrade pip requests setuptools pipenv
RUN pip3 install kubernetes==23.6.0
RUN pip3 install python-crontab==2.6.0
RUN pip3 install croniter==1.3.5

ADD schedule_scaling /root/schedule_scaling
COPY ./run_missed_jobs.py /root
RUN chmod a+x /root/run_missed_jobs.py
COPY ./startup.sh /root
RUN chmod a+x /root/startup.sh
CMD /root/startup.sh
