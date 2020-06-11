FROM python:3.8-alpine

RUN apk add --no-cache bash
RUN pip install pykube python-crontab

ADD schedule_scaling /root/schedule_scaling

ENV PYTHONPATH "${PYTHONPATH}:/root/schedule_scaling"
CMD /root/schedule_scaling/scripts/startup.sh
