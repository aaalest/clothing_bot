import time

import cv2
import numpy as np
# from PIL import Image
from mediapipe import solutions
from ultralytics import YOLO

from config import config


class Mask:
    def __init__(self):
        self.segmentation_model = None

    def load_segmentation_model(self):
        self.segmentation_model = YOLO(config.model.yolo_path)
        print('Segmentation model loaded')

    def run_yolo(self, img: np.ndarray) -> list:
        predictions = self.segmentation_model.predict(
            source=img,
            show=False,
            save=False,
            show_labels=True,
            show_conf=True,
            conf=0.4,
            save_txt=False,
            save_crop=False,
            line_width=1
        )
        return predictions

    def overlay_mask(self, img: np.ndarray, mask: np.ndarray, color: np.ndarray, alpha: float = .7) -> np.ndarray:
        # Ensure color is a single-row array for broadcasting
        color = np.array(color, dtype=np.uint8).reshape(1, -1)

        # Resize the single-channel mask to match the image size
        try:
            h, w, _ = img.shape
        except ValueError:
            h, w = img.shape
        resized_mask = cv2.resize(mask, (w, h))

        # Create a boolean mask for the current mask
        bool_mask = resized_mask > 0

        # Create a 3-channel mask from the single-channel boolean mask
        mask_img = np.stack([bool_mask] * 3, axis=-1)

        # Apply color to the mask
        mask_color = mask_img * color

        # Blend the mask with the image
        img = np.where(mask_img, img * (1 - alpha) + mask_color * alpha, img).astype(np.uint8)

        return img

    def reshape_img_to_square(self, img: np.ndarray) -> np.ndarray:
        # add black padding to make the image square
        print(f'input img shape: {img.shape}')
        height, width, _ = img.shape
        if height < width:
            diff = int((width - height) / 2)
            blank = np.zeros((diff, width, 3), dtype=np.uint8)
            img = np.vstack((img, blank))
            img = np.vstack((blank, img))
        elif height > width:
            diff = int((height - width) / 2)
            blank = np.zeros((height, diff, 3), dtype=np.uint8)
            img = np.hstack((img, blank))
            img = np.hstack((blank, img))
        print(f'output img shape: {img.shape}')
        return img

    def reshape_masks_to_original(self, img: np.ndarray, masks: dict) -> dict:
        height, width, _ = img.shape
        for mask_name, mask in masks.items():
            mask_h, mask_w = mask.shape

            if mask_h > height:
                mask = mask[int((mask_h - height) / 2):int(mask_h - (mask_h - height) / 2), :]
            if mask_w > width:
                mask = mask[:, int((mask_w - width) / 2):int(mask_w - (mask_w - width) / 2)]

            masks[mask_name] = mask
        return masks

    def crop_img_based_on_mask(self, img: np.ndarray, mask: np.ndarray, expand_by: float = 0.1) -> tuple:
        # show mask
        mask = mask.copy()

        # get min and max where mask is not black
        mask_x1 = np.min(np.where(mask > 0)[1])
        mask_y1 = np.min(np.where(mask > 0)[0])
        mask_x2 = np.max(np.where(mask > 0)[1])
        mask_y2 = np.max(np.where(mask > 0)[0])
        print(f'mask_x1: {mask_x1}, mask_y1: {mask_y1}, mask_x2: {mask_x2}, mask_y2: {mask_y2}')

        mask_x1 -= int(mask.shape[1] * expand_by)
        mask_y1 -= int(mask.shape[0] * expand_by)
        mask_x2 += int(mask.shape[1] * expand_by)
        mask_y2 += int(mask.shape[0] * expand_by)

        if mask_x1 < 0:
            mask_x1 = 0
        if mask_y1 < 0:
            mask_y1 = 0
        if mask_x2 > mask.shape[1]:
            mask_x2 = mask.shape[1]
        if mask_y2 > mask.shape[0]:
            mask_y2 = mask.shape[0]

        cropped_mask = mask[mask_y1:mask_y2, mask_x1:mask_x2].copy()
        cropped_img = img[mask_y1:mask_y2, mask_x1:mask_x2].copy()
        return cropped_img, cropped_mask, {'x1': mask_x1, 'y1': mask_y1, 'x2': mask_x2, 'y2': mask_y2}

    def generate_masks(self, img: np.ndarray) -> dict:
        now = time.time()
        predictions = self.run_yolo(self.reshape_img_to_square(img))
        print(f'Run YOLO time: {time.time() - now} seconds')

        if predictions[0].masks is None:
            raise Exception('Clothing not detected')
        for prediction in predictions:
            orig_img = prediction.orig_img
            img_copy = orig_img.copy()  # Create a copy of the original image to draw on
            height, width, _ = orig_img.shape  # Height and width of the image

            # Extracting data from predictions
            structured_masks = prediction.masks
            np_masks = prediction.masks.data.int().cpu().numpy().astype('uint8')
            names = prediction.names
            colors = np.random.uniform(0, 255,
                                       size=(len(structured_masks), 3))  # generate random colors for each prediction
            print(f'Colors: {colors}')
            print(f'Detected {len(structured_masks)} objects')

            masks = {}
            for i, box in enumerate(prediction.boxes):
                cls_id = box.cls.cpu().item()  # Convert to Python number
                cls_conf = box.conf.cpu().item()  # Convert to Python number
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()  # Convert to numpy array
                label = names[int(cls_id)]

                #  Draw mask
                np_mask = np_masks[i]

                masks = self.combine_masks(masks, np_mask, label)
                img_copy = self.overlay_mask(img_copy, np_mask, colors[i] * 0.7, alpha=0.6)

                # Draw bounding box
                start_point = (int(x1), int(y1))
                end_point = (int(x2), int(y2))
                line_width = 1
                img_copy = cv2.rectangle(img_copy, start_point, end_point, colors[i] * 1.3, line_width)

                # Annotate with label and confidence
                cv2.putText(img_copy, f'{label}: {cls_conf:.2f}', (int(x1), int(y1) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            colors[i], 2)

            # clothing_mask = overlay_mask(clothing_mask, clothing_mask, colors[i] * 0.7, alpha=0.6)

            # cv2.imshow('YOLO Predictions', img_copy)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            if 'clothing' not in masks:
                raise Exception('Clothing mask not detected')
            masks = self.modify_masks(img, masks)

            # cv2.imshow('clothing mask', expanded_masks["clothing"])
            # resized_img_copy = cv2.resize(img_copy, (0, 0), fx=0.5, fy=0.5)
            # img_copy = cv2.resize(img_copy, (1024, 1024))
            # cv2.imshow('YOLO Predictions', img_copy)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            # resize mask to original image size
            for mask_name, mask in masks.items():
                masks[mask_name] = cv2.resize(mask, (width, height))
            return self.reshape_masks_to_original(img, masks)

    def combine_masks(self, masks: dict, mask: np.ndarray, mask_name) -> dict:
        if mask_name not in masks:
            masks[mask_name] = mask.copy()
        else:
            masks[mask_name] = cv2.bitwise_or(masks[mask_name], mask.copy())
        return masks

    def modify_masks(self, img: np.ndarray, masks: dict, expand_by: float = 0.07) -> dict:
        img = img.copy()
        square_img = self.reshape_img_to_square(img)
        for mask_name, np_mask in masks.items():
            masks[mask_name] = (np_mask * 255).astype(np.uint8)  # Ensure masks are in uint8 format

        # Calculate the blur radius based on image dimensions and expansion factor
        clothing_mask_x1 = np.min(np.where(masks["clothing"] > 0)[1])
        clothing_mask_y1 = np.min(np.where(masks["clothing"] > 0)[0])
        clothing_mask_x2 = np.max(np.where(masks["clothing"] > 0)[1])
        clothing_mask_y2 = np.max(np.where(masks["clothing"] > 0)[0])
        height = clothing_mask_y2 - clothing_mask_y1
        width = clothing_mask_x2 - clothing_mask_x1
        blur_radius = int(max(height, width) * expand_by)
        if blur_radius % 2 == 0:
            blur_radius += 1
        if blur_radius <= 0:
            blur_radius = 1
        kernel_size = (blur_radius, blur_radius)
        circular_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)

        filled_face_mask = np.zeros((square_img.shape[0], square_img.shape[1]), dtype=np.uint8)
        if 'skin' in masks:
            masks["combined"] = cv2.bitwise_or(masks["clothing"], masks["skin"])

            # get min max x y of masks["skin"]
            scaled_skin_mask = cv2.resize(masks["skin"], (square_img.shape[1], square_img.shape[0]))
            skin_min_x = min(np.where(scaled_skin_mask > 0)[1])
            skin_max_x = max(np.where(scaled_skin_mask > 0)[1])
            skin_min_y = min(np.where(scaled_skin_mask > 0)[0])
            skin_max_y = max(np.where(scaled_skin_mask > 0)[0])
            y_diff = skin_max_y - skin_min_y

            print(f'square_img.shape[1], square_img.shape[0]: {square_img.shape[1], square_img.shape[0]}')
            print(f'skin_min_x: {skin_min_x}, skin_max_x: {skin_max_x}, skin_min_y: {skin_min_y}, skin_max_y: {skin_max_y}')
            face_detection_area = square_img[skin_min_y:y_diff, skin_min_x:skin_max_x]
            face_mask = np.zeros((face_detection_area.shape[0], face_detection_area.shape[1]), dtype=np.uint8)

            # Detect face landmarks
            results = None
            if face_detection_area.shape[0] > 0 and face_detection_area.shape[1] > 0:
                with solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=9,
                                                  min_detection_confidence=0.3) as face_mesh:
                    results = face_mesh.process(face_detection_area)
                    print(f'Face detection area shape: {face_detection_area.shape}')
            else:
                print('Face detection area has zero width or height, skipping face detection for this frame.')

            # Draw face landmarks
            if results and results.multi_face_landmarks:
                print(f'Found {len(results.multi_face_landmarks)} faces')

                for face_landmarks in results.multi_face_landmarks:
                    pts = np.array([np.multiply([lm.x, lm.y], [face_detection_area.shape[1], face_detection_area.shape[0]]).astype(int) for lm in face_landmarks.landmark])
                    hull = cv2.convexHull(pts)
                    cv2.fillConvexPoly(face_mask, hull, 255)
                filled_face_mask[skin_min_y:y_diff, skin_min_x:skin_max_x] = face_mask
        else:
            print('No skin mask detected, skipping face detection.')
            masks["combined"] = masks["clothing"].copy()

        # Dilate and blur the mask
        masks["clothing"] = cv2.dilate(masks["clothing"], circular_kernel, iterations=1)

        masks["clothing"] = cv2.resize(masks["clothing"], (square_img.shape[1], square_img.shape[0]))
        print(f'clothing_mask shape: {masks["clothing"].shape}')
        masks["clothing"] = np.where(filled_face_mask == 255, 0, masks["clothing"])
        masks["clothing"] = cv2.resize(masks["clothing"], (masks["combined"].shape[1], masks["combined"].shape[0]))
        masks["clothing"] = cv2.GaussianBlur(masks["clothing"], kernel_size, 0)
        return masks

    def expand_mask_alternative(self, masks: dict, expand_by: float = 0.05) -> dict:
        time_start = time.time()
        for mask_name, np_mask in masks.items():
            masks[mask_name] = (np_mask * 255).astype(np.uint8)  # Ensure masks are in uint8 format

        # Calculate the blur radius based on image dimensions and expansion factor
        height, width = masks["clothing"].shape[:2]
        expand_by /= 2
        expand_radius = int(max(height, width) * expand_by)
        blur_radius = int(max(height, width) * expand_by * 5)
        if blur_radius % 2 == 0:
            blur_radius += 1
        if blur_radius <= 0:
            blur_radius = 1
        expand_size = (expand_radius, expand_radius)
        blur_size = (blur_radius, blur_radius)

        circular_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, expand_size)

        masks["combined"] = cv2.bitwise_or(masks["clothing"], masks["skin"])

        # Dilate and blur the mask
        masks["clothing"] = cv2.dilate(masks["clothing"], circular_kernel, iterations=2)
        # masks["clothing"] = cv2.GaussianBlur(masks["clothing"], blur_size, 0)

        masks["clothing"] = cv2.bitwise_and(masks["clothing"], masks["combined"])

        masks["clothing"] = cv2.dilate(masks["clothing"], circular_kernel, iterations=2)
        masks["clothing"] = cv2.GaussianBlur(masks["clothing"], blur_size, 0)

        print(f'Expand mask time: {time.time() - time_start} seconds')

        # make masks["skin"] smaller by bluring and thresholding it
        # masks["skin"] = cv2.GaussianBlur(masks["skin"], (skin_kernel_size, skin_kernel_size), 0)
        # _, masks["skin"] = cv2.threshold(masks["skin"], 254, 255, cv2.THRESH_BINARY)

        # Invert the 'skin' mask
        # inverse_skin_mask = cv2.bitwise_not(masks["skin"])

        # Remove the 'clothing' mask where there is a 'skin' mask
        # masks["clothing"] = cv2.bitwise_and(masks["clothing"], inverse_skin_mask)

        # masks["clothing"] = cv2.GaussianBlur(masks["clothing"], (27, 27), 0)

        return masks
