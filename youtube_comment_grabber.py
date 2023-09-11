import os
from googleapiclient.discovery import build
from datetime import datetime
from pytz import timezone,utc
from dotenv import load_dotenv

from stuff import handle_video_ids

verbose = False

# clear arrays for ids
video_id_with_new = []
video_id_errors = []
video_id_counter = 0

# load from the module
# sign-up on google api for the youtube data api v3
# see readme.md for instructions
#
try:
	load_dotenv('.env')
except:
	print("You need to create a .env file.")
	exit()

# YouTube Data API V3
yt_api_key = os.getenv('YT_API_KEY')
if (yt_api_key == None):
	print("Set YT_API_KEY in the .env file")
	exit()

# Timey Whimey Stuff
try:
	local_timezone = timezone(os.getenv('local_timezone'))
except:
	print("ptzy is not happy with timezone string")
	exit()

## This is the compare time. 
#last_date_check = datetime.now()
#last_date_check = datetime.strptime("2023-08-01 12:23:34", "%Y-%m-%d %H:%M:%S") # in America/Chicago timezone
#last_date_check_utc = local_timezone.localize(last_date_check).astimezone(utc)
with open("last_check.txt", 'r') as infile:
	file_string = infile.read().strip()
last_date_check = datetime.strptime(file_string, "%Y-%m-%d %H:%M:%S") # in America/Chicago timezone
last_date_check_utc = local_timezone.localize(last_date_check).astimezone(utc)

# just in case we miss a comment by a second
with open("last_check.txt",'w') as outfile:
	outfile.write(datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S"))

def video_comments(video_id, verbose=verbose):
	global video_id_with_new
	global video_id_counter

	# give update something is happening
	video_id_counter = video_id_counter + 1
	if (video_id_counter >= 10):
		print(".")
		video_id_counter = 0
	else:
		print(".", end='', flush=True)

	if (verbose): print(f"Handling: https://www.youtube.com/watch?v={video_id}")

	# creating youtube resource object
	youtube = build('youtube', 'v3', developerKey=yt_api_key)

	# retrieve youtube video results
	video_response=youtube.commentThreads().list(
	part='snippet,replies',
	videoId=video_id
	).execute()
	#video_response = handle_video_ids.yt_api_query(video_id, yt_api_key)

#	print(type(video_response))

	# iterate video response
	new_comment = False
	new_reply = False
	while video_response:
	
		# extracting required info
		# from each result object
		for item in video_response['items']:
			# moderationStatus requires authorization (e.g. channel owner)
			# Extacting comments

			# top level things
			comment_id = item['snippet']['topLevelComment']['id']
			replycount = item['snippet']['totalReplyCount']

			# snippet level
			cs = item['snippet']['topLevelComment']['snippet'] #comment_snippet
			#comment = item['snippet']['topLevelComment']['snippet']['textDisplay']

			# make nice clean string if it has been edited
			comment_datetime_object = utc.localize(datetime.strptime(cs['updatedAt'], "%Y-%m-%dT%H:%M:%SZ"))
			if (comment_datetime_object > last_date_check_utc): new_comment = True

			publish_string = f"Published: {cs['publishedAt']}"
			if (cs['publishedAt'] != cs['updatedAt']):
				# hey, they made an edit!
				publish_string = f"{publish_string}, Edited: {cs['updatedAt']}"

			if (verbose): print(f"({comment_id}): {replycount} replies, Published: {cs['publishedAt']}") 
			if (verbose): print(f"[{cs['authorDisplayName']}]: {cs['textDisplay']}") 
			# if reply is there
			
			if (replycount > 0):
				# iterate through all reply
				for reply in item['replies']['comments']:
					id = item['id']
					rs = reply['snippet']

					reply_datetime_object = utc.localize(datetime.strptime(cs['updatedAt'], "%Y-%m-%dT%H:%M:%SZ"))
					if (reply_datetime_object > last_date_check_utc): new_reply = True

					if (verbose): print(f"	[{id}, {rs['authorDisplayName']}]: {rs['textDisplay']}")
					reply_publish_string = f"[rs['idPublished: {rs['publishedAt']}"
					if (rs['publishedAt'] != rs['updatedAt']):
						reply_publish_string = f"{reply_publish_string}, Edited: {rs['updatedAt']}"

					if (verbose): print(f"	{reply_publish_string}")
			if (verbose): print('\n')

		# Again repeat
		if 'nextPageToken' in video_response:
			video_response = youtube.commentThreads().list(
					part = 'snippet,replies',
					videoId = video_id,
					pageToken = video_response['nextPageToken']
				).execute()
		else:
			break
	if (new_comment or new_reply):
		#print(f"New Comment or reply: https://youtube.com/watch?v={video_id}")
		video_id_with_new.append(video_id)

def print_id_with_urL(video_ids):
	for video_id in video_ids:
		print(f"https://youtube.com/watch?v={video_id}")

def main():
	global youtube
	global video_id_with_new
	global video_id_errors
	# Temporary single id

	print(f"Checking for comments since {last_date_check.strftime('%Y-%m-%d %H:%M:%S')}")
	video_ids = handle_video_ids.load_video_ids(verbose=True)
	if (len(video_ids) > 0):
		for video_id in video_ids:
			# reset the youtube object
			youtube = ""
			if (verbose): print(f'\n\n---------- Getting Comments for {video_id} ----------')
			try:
				video_comments(video_id)
			except Exception as e:
				print("Exception!")
				video_id_errors.append(video_id)

	if (len(video_id_with_new) > 0):
		print("Videos with new comments or replies:")
		print_id_with_urL(video_id_with_new)
		print("\n")

	if (len(video_id_errors) > 0):
		print("ERROR WITH THESE:")
		print_id_with_urL(video_id_errors)
		print("\n")

	#video_id = "bqdyve-hhZY"

	# Call function
	# print(f'\n\n---------- Getting Comments for {video_id} ----------')
	# video_comments(video_id)

if __name__ == '__main__':
	main()



# Originally based this example:
# https://www.geeksforgeeks.org/how-to-extract-youtube-comments-using-youtube-api-python/

# Copyright (c) 2023 James Lewis (@baldengineer)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.