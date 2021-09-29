FROM python:latest

ENV URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"

RUN mkdir /tmp/aws \
  && curl "$URL" -o "/tmp/aws/awscliv2.zip" \
  && unzip -d /tmp/aws /tmp/aws/awscliv2.zip \
  && /tmp/aws/aws/install \
  && rm -rf /tmp/aws

CMD bash
