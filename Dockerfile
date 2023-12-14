FROM python:3.12-slim

EXPOSE 5000

WORKDIR /opt/equipment-availability-service

COPY . /opt/equipment-availability-service/

RUN pip install -r requirements.txt -e .

ENTRYPOINT ["equipment-availability-service"]
