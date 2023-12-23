FROM python:3-alpine

LABEL maintainer='<author>'
LABEL version='0.0.0-dev.0-build.0'

ADD . /code
WORKDIR /code
RUN \
  apk add --no-cache libc-dev libffi-dev gcc && \
  pip install -r requirements.txt --no-cache-dir && \
  apk del gcc libc-dev libffi-dev && \
  addgroup iewt && \
  adduser -Ss /bin/false -g iewt iewt && \
  chown -R iewt:iewt /code

EXPOSE 8888/tcp
USER iewt
CMD ["python", "run.py"]
