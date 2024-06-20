FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

WORKDIR /usr/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

ENV TZ="Europe"
ENV PYTHONPATH=/usr/app/src

WORKDIR /usr/app/src
CMD ["python", "main.py"]

#docker build -t clothingbot_telegram . && docker run -p 27017:27017 -t clothingbot_telegram