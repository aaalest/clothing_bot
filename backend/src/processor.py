import time
from typing import Literal
import cv2
import numpy as np
import webuiapi
from PIL import Image
from PIL import ImageOps
from pydantic import BaseModel
import requests
import base64
import os

from mask import Mask

mask = Mask()
mask.load_segmentation_model()
url = "http://127.0.0.1:7860"

# api = webuiapi.WebUIApi(host='host.docker.internal', port=7860)
if os.path.exists('/.dockerenv'):
    api = webuiapi.WebUIApi(host='host.docker.internal', port=7860)
else:
    api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
# api = webuiapi.WebUIApi(host='1273333.0.0.1', port=7860)


class ProcessData(BaseModel):
    upper: Literal['jacket', 't-shirt', 'shirt', 'sweater', 'hoodie', 'coat', 'dress']
    upper_color: Literal['auto', 'black', 'white', 'red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray']
    lower: Literal['jeans', 'trousers', 'shorts', 'skirts']
    lower_color: Literal['auto', 'black', 'white', 'red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'gray']
    style: Literal['auto', 'casual', 'sport', 'formal', 'party']


def generate(img: np.ndarray, data: ProcessData) -> np.ndarray:
    now = time.time()
    masks = mask.generate_masks(img)
    print(f'generate_masks time: {time.time() - now}')
    cropped_img, cropped_mask, crop_info = mask.crop_img_based_on_mask(img, masks["combined"])
    # cropped_mask = masks["clothing"].copy()[crop_info["y1"]:crop_info["y2"], crop_info["x1"]:crop_info["x2"]]
    print(f'zoom_out_img time: {time.time() - now}')
    controlnet_units = get_controlnet_units(cropped_img)
    positive_prompt, negative_prompt = get_prompts(data)
    resolution = 512
    # resolution = 768
    # resolution = 1024

    width, height = calculate_dimensions(cropped_img.shape[1] / cropped_img.shape[0], resolution)
    print(f'Generating at resolution: {width}x{height}')

    # cv2.imshow('img', img)
    # cv2.imshow('mask', masks["clothing"].copy())
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    generation = api.img2img(
        prompt=positive_prompt,
        negative_prompt=negative_prompt,
        mask_image=Image.fromarray(masks["clothing"].copy()),
        inpaint_full_res=True,
        inpaint_full_res_padding=32,
        images=[Image.fromarray(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))],
        override_settings={"sd_model_checkpoint": 'realisticVisionV60B1_v51HyperInpaintVAE.safetensors'},
        controlnet_units=controlnet_units,
        # controlnet_units=[],
        # seed=-1,
        cfg_scale=7,
        sampler_index='Euler a',
        # sampler_index='DPM++ 2M Karras',
        denoising_strength=1,
        width=width,
        height=height,
        steps=16,
        batch_size=1
    )

    result = cv2.cvtColor(np.array(generation.images[0]), cv2.COLOR_RGB2BGR)

    print(f'generate time: {time.time() - now}')
    return result


def reshape_img_to_square(img: Image) -> Image:
    # Calculate the difference between width and height
    diff = abs(img.size[0] - img.size[1])

    if img.size[0] < img.size[1]:  # If the width is smaller, add padding to left and right
        padding = (diff // 2, 0, diff - diff // 2, 0)
    else:  # If the height is smaller, add padding to top and bottom
        padding = (0, diff // 2, 0, diff - diff // 2)

    # Add padding to the image and return
    return ImageOps.expand(img, padding, fill='black')


def get_controlnet_units(cropped_img: np.ndarray):
    unit_pose = webuiapi.ControlNetUnit(input_image=Image.fromarray(cropped_img), module='dw_openpose_full', model='control_v11p_sd15_openpose [cab727d4]', weight=0.8)
    # self.unit_pose = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='openpose_full', model='control_v11p_sd15_openpose [cab727d4]', weight=0.8)
    # self.unit_pose = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='openpose_full', model='control_v11p_sd15_openpose [cab727d4]', weight=1)
    # self.unit_pose = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='openpose', model='control_v11p_sd15_openpose [cab727d4]', weight=0.75)
    # self.unit_densepose = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='densepose_parula (black bg & blue torso)', model='control_v11p_sd15_openpose [cab727d4]')
    # self.unit_depth = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='depth_zoe', model='control_v11f1p_sd15_depth [cfd03158]', weight=0.4)
    # unit_map = webuiapi.ControlNetUnit(input_image=Image.fromarray(cropped_img), module='normal_bae',
    #                                         model='control_v11p_sd15_normalbae [316696f1]', weight=0.5)
    # self.unit_softedge = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='softedge_pidisafe', model='control_v11p_sd15_softedge [a8575a2a]', weight=0.25)
    # self.unit_segmentation = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='seg_ofade20k', model='control_v11p_sd15_seg [e1f51eb9]')
    # self.unit_linear = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), module='lineart_standard (from white bg & black line)', model='control_v11p_sd15_lineart [43d4be0d]', weight=0.5)
    # self.unit_outfit = webuiapi.ControlNetUnit(input_image=Image.fromarray(self.cropped_img), model='outfitToOutfit_v10 [df89ff56]')

    # controlnet_units = [self.unit_depth]
    # controlnet_units = [self.unit_map, self.unit_pose]
    # controlnet_units = [unit_map]
    controlnet_units = [unit_pose]
    # controlnet_units = []
    return controlnet_units


def get_prompts(data: ProcessData):
    upper_color = data.upper_color
    if data.upper_color == 'auto':
        upper_color = ''
    else:
        upper_color = f'{upper_color} '

    lower_color = data.lower_color
    if data.lower_color == 'auto':
        lower_color = ''
    else:
        lower_color = f'{lower_color} '

    style = data.style
    if data.style == 'auto':
        style = ''
    else:
        style = f'{style}, '

    positive_prompt = f'((clothing)), {style}{upper_color}{data.upper}, {lower_color}{data.lower}'
    print(f'positive_prompt: {positive_prompt}')
    negative_prompt = ''

    return positive_prompt, negative_prompt


def calculate_dimensions(image_ratio, target_resolution):
    target_resolution **= 2
    # Calculate initial width and height based on the image ratio
    height = (target_resolution / image_ratio) ** 0.5
    width = height * image_ratio

    # Adjusting width and height to closely match the target resolution
    # without exceeding it
    while width * height > target_resolution:
        width -= 1
        height = width / image_ratio

    return round(width), round(height)

