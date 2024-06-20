# Description: Dockerfile for stable-diffusion-webui/stable-diffusion-webui-forge (automatic1111 version) for clothing bot
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as python3.10-base

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update sources list to use alternative mirror and install system dependencies
RUN apt-get update --fix-missing
RUN apt-get install -y --no-install-recommends build-essential python3-venv python3-pip python3-dev libgl1 libglib2.0-0
RUN apt-get install -y git curl libgoogle-perftools-dev wget
RUN rm -rf /var/lib/apt/lists/*

# Add a non-root user and switch to that user
RUN useradd -ms /bin/bash appuser

WORKDIR /home/appuser
USER appuser
ENV HOME /home/appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /home/appuser
#RUN git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui  # original automatic1111 version
RUN git clone https://github.com/lllyasviel/stable-diffusion-webui-forge && mv stable-diffusion-webui-forge stable-diffusion-webui  # forge automatic1111 version

WORKDIR /home/appuser/stable-diffusion-webui/models/Stable-diffusion

RUN wget --content-disposition 'https://huggingface.co/qnzkzpwldns/uber/resolve/main/inpainting/realisticVisionV60B1_v51HyperInpaintVAE-inpainting.safetensors'
RUN mv realisticVisionV60B1_v51HyperInpaintVAE-inpainting.safetensors realisticVisionV60B1_v51HyperInpaintVAE.safetensors
RUN ls -lha

# if you are using automatic1111 version you need to also install controlnet
#WORKDIR /home/appuser/stable-diffusion-webui/extensions
#RUN git clone https://github.com/Mikubill/sd-webui-controlnet

WORKDIR /home/appuser/stable-diffusion-webui/models/ControlNet
RUN wget --content-disposition 'https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.pth'  # control_v11p_sd15_openpose.pth
RUN ls -lha

WORKDIR /home/appuser/stable-diffusion-webui

# Expose the port the app runs on
EXPOSE 7860

ENTRYPOINT ./webui.sh --listen --api --pin-shared-memory --cuda-malloc --cuda-stream

#docker volume create --driver local --opt type=none --opt device=<path_to_storage> --opt o=bind a1111_clotingbot_storage
#docker build -t a1111_clotingbot . && docker run --gpus all -p 7860:7860 --shm-size=8g -v a1111_clotingbot_storage:/home/appuser/stable-diffusion-webui -t a1111_clotingbot
