FROM docker.io/python:3.13-slim
MAINTAINER Computer Science House <webmaster@csh.rit.edu>

RUN mkdir /opt/selfservice

ADD requirements.txt /opt/selfservice

WORKDIR /opt/selfservice

RUN apt-get -yq update && \
    apt-get -yq install libsasl2-dev libldap2-dev libldap-common libssl-dev git gcc g++ make && \
    pip install -r requirements.txt && \
    apt-get -yq clean all

ADD . /opt/selfservice

EXPOSE 8080

CMD ["gunicorn", "selfservice:app", "--bind=0.0.0.0:8080", "--access-logfile=-", "--timeout=256"]

