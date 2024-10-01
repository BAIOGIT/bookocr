import cv2
import os

import argparse
import math, keras_ocr

import asyncio
from picwish import PicWish, OCRFormat, OCRLanguage

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--image', type=str, 
					help='path to image')
parser.add_argument('--thresh', type=int, default=15, 
					help='threshold to distinguish new rows')
parser.add_argument('--order', type=str, default='yes', 
					help='enter y or yes to order detections in a human readable way')
args = parser.parse_args()

def extract_frames(video_path):
	# Initialize the video capture object
	cap = cv2.VideoCapture(video_path)
	frames = []
	frame_number = 0
	
	# Get the original fps of the video
	original_fps = cap.get(cv2.CAP_PROP_FPS)
	
	# Calculate the interval between frames to achieve the target fps
	frame_interval = int(original_fps // 30)
	
	# Check if video file opened successfully
	if not cap.isOpened():
		print(f"Error: Cannot open video file {video_path}")
		return []

		# Loop through the video frames
	while cap.isOpened():                        
		ret, frame = cap.read()  # Read a frame
		if not ret:  # If no frame is returned, we've reached the end of the video
			break
		
		if frame_number >= 85 and frame_number <= 475:    
		# if frame_number > 149 and frame_number < 151:  
		# if frame_number > 496 and frame_number < 498:  
			if frame_number % frame_interval == 0:    
				# Resize the frame to one-third of its original size.2
				height, width, channels = frame.shape
				new_width = width // 3
				new_height = height // 3
				
				denoised_frame = cv2.fastNlMeansDenoising(frame, h = 3)
				gray_frame = cv2.cvtColor(denoised_frame, cv2.COLOR_BGR2GRAY)

				# laplacian_frame = cv2.Laplacian(gray_frame, cv2.CV_64F)
				# variance = laplacian_frame.var()
				# print(f"Frame {frame_number} variance --> {variance}")

				# contrast_frame = cv2.equalizeHist(gray_frame)
				contrast_frame = cv2.adaptiveThreshold(gray_frame, 255,
														cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
														cv2.THRESH_BINARY, 11, 2)

				# thresh1 = 127
				# thresh2 = 255
				# contrast_frame = cv2.threshold(gray_frame, thresh1, thresh2, cv2.THRESH_BINARY + cv2.THRESH_OTSU)	
				
				edited_frame = contrast_frame

				resized_frame = edited_frame
				# resized_frame = cv2.resize(edited_frame, (new_width, new_height))
				
				# Print the original and resized frame sizes
				# print(f"Frame {frame_number}: Original Size = {width}x{height}, Resized Size = {new_width}x{new_height}")
				
				# Show the resized frame
				cv2.imshow("Frame", resized_frame)
				
				# Store the current frame with its frame number
				frames.append((frame_number, resized_frame))
			
				# Wait for the spacebar to proceed to the next frame or 'q' to quit
				key = cv2.waitKey(0) & 0xFF
				if key == ord('q'):  # Press 'q' to quit
					print("Interruption by user. Exiting...")
					break
				elif key == ord(' '):  # Press spacebar to proceed
					continue
			
		frame_number += 1
		
	cap.release()  # Release the video capture object
	cv2.destroyAllWindows()  # Close any OpenCV windows
	
	# Save the resized frames as images
	frame_filepath = "./results/04"
	os.makedirs(frame_filepath, exist_ok=True)
	
	for i, (frame_number, frame) in enumerate(frames):
		frame_filename = os.path.join(frame_filepath, f"frame_{frame_number}.jpg")
		cv2.imwrite(frame_filename, frame)
		
	return frames

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
	Function returns list of dictionaries with (key,value):
		* text : detected text in image
		* center_x : center of bounding box (x)
		* center_y : center of bounding box (y)
		* distance_from_origin : hypotenuse
		* distance_y : distance between y and origin (0,0)
	...for each bounding box (detections). 
	"""

	# Point of origin
	x0, y0 = 0, 0 

	# Generate dictionary
	detections = []
	for group in predictions:
		
		# Get center point of bounding box
		top_left_x, top_left_y = group[1][0]
		bottom_right_x, bottom_right_y = group[1][1]
		center_x, center_y = (top_left_x + bottom_right_x)/2, (top_left_y + bottom_right_y)/2
	
		# Use the Pythagorean Theorem to solve for distance from origin
		distance_from_origin = math.dist([x0,y0], [center_x, center_y])

		# Calculate difference between y and origin to get unique rows
		distance_y = center_y - y0
		
		# Append all results
		detections.append({
							'text': group[0], 
							'center_x': center_x, 
							'center_y': center_y, 
							'distance_from_origin': distance_from_origin,
							'distance_y': distance_y
						})
	
	return detections 


def distinguish_rows(lst, thresh=15):
	"""Function to help distinguish unique rows"""
	sublists = []
	for i in range(0, len(lst)-1):
		if (lst[i+1]['distance_y'] - lst[i]['distance_y'] <= thresh):
			if lst[i] not in sublists:
				sublists.append(lst[i])
			sublists.append(lst[i+1])
		else:
			yield sublists
			sublists = [lst[i+1]]
	yield sublists

# def main(image_path, thresh, order='yes'):
# 	"""Function returns predictions from left to right & top to bottom"""
# 	predictions = detect_w_keras(image_path)
# 	predictions = get_distance(predictions)
# 	predictions = list(distinguish_rows(predictions, thresh))
	
# 	# Remove all empty rows
# 	predictions = list(filter(lambda x:x!=[], predictions))

# 	# Order text detections in human readable format
# 	ordered_preds = []
# 	ylst = ['yes', 'y']
# 	for row in predictions:
# 		if order in ylst: row = sorted(row, key=lambda x:x['distance_from_origin'])
# 		for each in row: ordered_preds.append(each['text'])
	
# 	return ordered_preds

async def main(image):
	picwish = PicWish()
	ocr_result = await picwish.ocr(
		image,
		format=OCRFormat.TXT,
		languages=[OCRLanguage.ITALIAN, OCRLanguage.ENGLISH, OCRLanguage.DIGITS]
	)
	print(await ocr_result.text())
	
if __name__=='__main__':
	picwish = PicWish()
	# asyncio.run(main('./results/01/frame_497.jpg'))
 
	# thresh = args.thresh
	# order = args.order
 
	video_path = './media/IMG_9452.mov'
	dirpath = './results/04'
	frames = extract_frames(video_path)
	
	# for i, (frame_number, frame) in enumerate(frames):
	# 	print(f'Generating predictions for frame {frame_number}...')

	# 	# predictions = main(frame, thresh, order)
	# 	# print(predictions)

	# 	asyncio.run(main(frame))

	# for filepath in os.listdir(dirpath):
	# 	try:
	# 		asyncio.run(main(os.path.join(dirpath, filepath)))
	# 	except:
	# 		pass