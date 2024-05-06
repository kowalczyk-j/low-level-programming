FROM python:3
WORKDIR /app  

COPY gateway /app

RUN pip install -r /app/requirements.txt

ENV PYTHONPATH "/app:${PYTHONPATH}"
  
ENTRYPOINT ["python", "/app/gateway.py"]
