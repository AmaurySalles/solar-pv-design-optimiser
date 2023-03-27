FROM python:3.10.6-slim-buster

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 80

ENTRYPOINT ["streamlit","run"]

CMD ["app.py", "--server.port=80", "--server.address=0.0.0.0"]
