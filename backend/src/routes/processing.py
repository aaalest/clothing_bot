from io import BytesIO

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, Request, HTTPException
from starlette.responses import Response, JSONResponse
import urllib.parse
import base64

import processor


processing_router = APIRouter(prefix='/processing')


@processing_router.post('/upload')
async def upload_image(image: UploadFile, request: Request) -> Response:
    # Directly access parameters from query_params, which is already a QueryParams object
    data_dict = dict({key: request.query_params[key] for key in request.query_params})
    for key, value in enumerate(data_dict):
        if data_dict[value] == 'None':
            data_dict[value] = None

    in_memory_file = BytesIO(await image.read())
    file_bytes = np.asarray(bytearray(in_memory_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # try:
    generated_img = processor.generate(img, processor.ProcessData(
        upper=data_dict["upper"],
        upper_color=data_dict["upper_color"],
        lower=data_dict["lower"],
        lower_color=data_dict["lower_color"],
        style=data_dict["style"]
    ))
    _, buf = cv2.imencode('.jpg', generated_img)
    base64_encoded_result = base64.b64encode(buf.tobytes()).decode()  # Encode bytes to base64 and decode to string
    return JSONResponse(content={"status": "success", "image": base64_encoded_result}, media_type="application/json")
    # except Exception as e:
    #     if str(e) == 'Clothing not detected':
    #         raise HTTPException(status_code=400, detail="clothing not found")
    #     else:
    #         print(f'Error: {e}')
    #         raise HTTPException(status_code=401, detail=str(e))
