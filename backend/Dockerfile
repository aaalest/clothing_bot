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

EXPOSE 7860

WORKDIR /usr/app/src
CMD ["python", "main.py"]

#docker build -t clothingbot_backend . && docker run -p 5678:5678 -p 7860:7860 -t clothingbot_backend
#docker build -t clothingbot_backend . && docker run -p 5678:5678 -e HOST_INTERNAL_URL=http://host.docker.internal:7860 -t clothingbot_backend

