import os
import numpy as np

import cv2
from skimage.metrics import structural_similarity as ssim
import pytesseract

import keras_ocr
import math

def extract_frames(video_path):
    # Initialize the video capture object
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_number = 0
    
    # Check if video file opened successfully
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}")
        return []

        # Loop through the video frames
    while cap.isOpened():                        
        ret, frame = cap.read()  # Read a frame
        if not ret:  # If no frame is returned, we've reached the end of the video
            break
        
        if frame_number > 550 and frame_number < 600:    
            # Resize the frame to one-third of its original size
            height, width, channels = frame.shape
            new_width = width // 3
            new_height = height // 3
            
            # resized_frame = cv2.resize(frame, (width, height))
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Print the original and resized frame sizes
            # print(f"Frame {frame_number}: Original Size = {width}x{height}, Resized Size = {new_width}x{new_height}")
            
            # Show the resized frame
            # cv2.imshow("Frame", resized_frame)
            
            # Store the current frame with its frame number
            frames.append((frame_number, resized_frame))
        
            # Wait for the spacebar to proceed to the next frame or 'q' to quit
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):  # Press 'q' to quit
                print("Interruption by user. Exiting...")
                break
            # elif key == ord(' '):  # Press spacebar to proceed
            #     continue
            
        frame_number += 1
        
    cap.release()  # Release the video capture object
    cv2.destroyAllWindows()  # Close any OpenCV windows

    # # Save the resized frames as images
    # frame_filepath = "./results/02"
    # os.makedirs(frame_filepath, exist_ok=True)
    
    # for i, (frame_number, frame) in enumerate(frames):
    #     frame_filename = os.path.join(frame_filepath, f"frame_{frame_number}.jpg")
    #     cv2.imwrite(frame_filename, frame)
        
    return frames

def detect_unique_pages(frames):
    unique_pages = []
    prev_frame = None

    for frame_number, frame in frames:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is None:
            unique_pages.append((frame_number, frame))
            prev_frame = gray_frame
            continue
        
        score = ssim(prev_frame, gray_frame)
        if score < 0.95:  # Threshold for uniqueness, tune as needed
            unique_pages.append((frame_number, frame))
            prev_frame = gray_frame

    for i, (page_number, page) in enumerate(unique_pages):
        print(f'{page_number}')
        
        cv2.imshow("Page", page)
        
        # Wait for the spacebar to proceed to the next frame or 'q' to quit
        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):  # Press 'q' to quit
            print("Interruption by user. Exiting...")
            break
        # elif frame_number == 600:  # Press spacebar to proceed
        #     break
        elif key == ord(' '):  # Press spacebar to proceed
            continue
        
    return unique_pages

def ocr_frames(frames):
    texts = []
    for i, (frame_number, frame) in enumerate(frames):
        text = pytesseract.image_to_string(frame)
        print(text)
        texts.append(text)
        
        cv2.imshow("Page", frame)
        
        # Wait for the spacebar to proceed to the next frame or 'q' to quit
        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):  # Press 'q' to quit
            print("Interruption by user. Exiting...")
            break
        # elif frame_number == 600:  # Press spacebar to proceed
        #     break
        elif key == ord(' '):  # Press spacebar to proceed
            continue
        
    return texts

def detect_w_keras(image_path):
    """Function returns detected text from image"""
   
    # Initialize pipeline
    pipeline = keras_ocr.pipeline.Pipeline()
    # Read in image path
    read_image = keras_ocr.tools.read(image_path)
    # prediction_groups is a list of (word, box) tuples
    prediction_groups = pipeline.recognize([read_image])
    return prediction_groups[0]

def get_distance(predictions):
    """
    Function returns dictionary with (key,value):
        * text : detected text in image
        * center_x : center of bounding box (x)
        * center_y : center of bounding box (y)
        * distance_from_origin : hypotenuse
        * distance_y : distance between y and origin (0,0)
    """
    
    # Point of origin
    x0, y0 = 0, 0
    # Generate dictionary
    detections = []
    for group in predictions:
        # Get center point of bounding box
        top_left_x, top_left_y = group[1][0]
        bottom_right_x, bottom_right_y = group[1][1]
        center_x = (top_left_x + bottom_right_x) / 2
        center_y = (top_left_y + bottom_right_y) / 2
    # Use the Pythagorean Theorem to solve for distance from origin
    distance_from_origin = math.dist([x0,y0], [center_x, center_y])
    # Calculate difference between y and origin to get unique rows
    distance_y = center_y - y0
    # Append all results
    detections.append({
                        'text':group[0],
                        'center_x':center_x,
                        'center_y':center_y,
                        'distance_from_origin':distance_from_origin,
                        'distance_y':distance_y
                    })
    return detections

def distinguish_rows(lst, thresh=15):
    """Function to help distinguish unique rows"""
    
    sublists = [] 
    for i in range(0, len(lst)-1):
        if lst[i+1]['distance_y'] - lst[i]['distance_y'] <= thresh:
            if lst[i] not in sublists:
                sublists.append(lst[i])
            sublists.append(lst[i+1])
        else:
            yield sublists
            sublists = [lst[i+1]]
    yield sublists
    
def main():
    # Example usage
    video_path = "./media/IMG_9452.mov"
    # frames = extract_frames(video_path)
    # texts = ocr_frames(frames)
    
    # for i, (frame_number, frame) in enumerate(frames):
    #     predictions = detect_w_keras(frame)
    #     predictions = get_distance(predictions)
    #     predictions = list(distinguish_rows(predictions, 15))
    #     # Remove all empty rows
    #     predictions = list(filter(lambda x:x!=[], predictions))
    #     # Order text detections in human readable format
    #     ordered_preds = []
    #     ylst = ['yes', 'y']
    #     for pr in predictions:
    #         if order in ylst: 
    #             row = sorted(pr, key=lambda x:x['distance_from_origin'])
    #             for each in row: 
    #                 ordered_preds.append(each['text'])
    #     return ordered_preds
        
    predictions = detect_w_keras("./results/02/frame_600.jpg")
    predictions = get_distance(predictions)
    predictions = list(distinguish_rows(predictions, 15))
    # Remove all empty rows
    predictions = list(filter(lambda x:x!=[], predictions))
    # Order text detections in human readable format
    ordered_preds = []
    ylst = ['yes', 'y']
    for pr in predictions:
        if order in ylst: 
            row = sorted(pr, key=lambda x:x['distance_from_origin'])
            for each in row: 
                ordered_preds.append(each['text'])
    return ordered_preds

if __name__ == "__main__":
    for pred in main():
        print(pred)