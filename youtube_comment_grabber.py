#!/usr/bin/python

import os
import sys
import traceback

from googleapiclient.discovery import build
from datetime import datetime
from pytz import timezone,utc
from dotenv import load_dotenv
from rich.progress import Progress

from helpers import handle_video_ids
from helpers import handle_video_descriptions
from helpers import db_ops

# TODO: Incorporate Rich (and maybe Textual) https://github.com/Textualize/rich

##### Globals
# clear arrays for ids
video_id_with_new = []
video_id_errors = []
video_id_counter = 0
time_at_launch = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S") # used later, get the time asap
time_at_launch_gmt = utc.localize(datetime.strptime(time_at_launch, "%Y-%m-%d %H:%M:%S")) # adds +00:00

verbose = False
no_last_update = False

def print_cmdline_help():
	print("This script supports these arguments:")
	print("  -q    only print list of URLs (and status)")
	print("  -noup does not update the last_check.txt file")
	print("  -h    this message")
	exit()

def check_cmdline_args():
	global verbose
	global no_last_update

	if ("-h" in sys.argv) or ("-H" in sys.argv): 
		print_cmdline_help()
	
	if ("-q" in sys.argv) or ("-Q" in sys.argv):
		verbose = False
		print("Hiding comments (and other stuff)")
	else:
		verbose = True
		print("Showing comments (and other stuff) use -q to ignore")
		
	if ('-noup' in sys.argv) or ('-NOUP' in sys.argv):
		no_last_update = True

	# -noup isn't here but it's going to change to a flag
	# anyway

# TODO move this to main() after the checks
check_cmdline_args()

# TODO: Move these checks to a function
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
	time_at_launch_gmt
except:
	print("ptzy is not happy with timezone string")
	exit()

def video_comments(video_id, last_date_check_utc, verbose=verbose):
	global video_id_with_new
	global video_id_counter

	# db_video_title = handle_video_descriptions.get_video_title_db(video_id)
	# print(f"Checking: [{db_video_title}]")
	# give update something is happening
	# video_id_counter = video_id_counter + 1
	# if (video_id_counter >= 10):
	# 	video_id_counter = 0
	#	print(".")
	# else:
	# 	print(".", end='', flush=True)

	#if (verbose): print(f"Handling: https://www.youtube.com/watch?v={video_id}")

	# creating youtube resource object
	youtube = build('youtube', 'v3', developerKey=yt_api_key)

	# retrieve youtube video results
	video_response=youtube.commentThreads().list(
	part='snippet,replies',
	videoId=video_id
	).execute()
	#video_response = handle_video_ids.yt_api_query(video_id, yt_api_key)

	# ! iterate video response
	new_comment = False
	new_reply = False
	#print(f"video_reponse is {sys.getsizeof(video_response)} bytes")
	while video_response:
		# extracting required info
		# from each result object
		#  Ref dec: https://developers.google.com/youtube/v3/docs/?apix=true
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
			if (comment_datetime_object > last_date_check_utc): 
				new_comment = True
				if (verbose): print(f"\n\nNew top comment on: https://www.youtube.com/watch?v={video_id}")
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

					reply_datetime_object = utc.localize(datetime.strptime(rs['updatedAt'], "%Y-%m-%dT%H:%M:%SZ"))
					if (reply_datetime_object > last_date_check_utc): 
						new_reply = True
						if (verbose): print(f"\n\tNew replies")
						if (verbose): print(f"\t[{rs['authorDisplayName']}]: {rs['textDisplay']}")
						reply_publish_string = f"[{id}] Published: {rs['publishedAt']}"
						if (rs['publishedAt'] != rs['updatedAt']):
							reply_publish_string = f"{reply_publish_string}, Edited: {rs['updatedAt']}"

						if (verbose): print(f"\t{reply_publish_string}\n")
			#if (verbose): print('\n')

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
	last_date_check_utc = None
	
	# bail if we can't open the db
	if (db_ops.create_connection() == False): exit()

	# update video descriptions. 
	# TODO: Need to check if comments changed!
	handle_video_descriptions.update_video_descriptions(time_at_launch_gmt)

	#! Date Check
	last_date_check = datetime.strptime(db_ops.get_last_comment_check(), "%Y-%m-%d %H:%M:%S") # in America/Chicago timezone
	last_date_check_utc = local_timezone.localize(last_date_check).astimezone(utc)
	print(f"Checking for comments since {last_date_check.strftime('%Y-%m-%d %H:%M:%S')}")
	if (no_last_update):
		print(f"Not updating last check date")
	else:
		print(f"Updating last check date to {time_at_launch}. Use -noup to skip this.")
		# just in case we miss a comment by a second
		db_ops.set_last_comment_check(time_at_launch)

	video_ids = db_ops.db_get_video_ids(True)
	if (len(video_ids) > 0):
		with Progress() as progress:
			task = progress.add_task("Checking for comments", total=len(video_ids))
			for video_id in video_ids:
				# give pretty update status
				db_video_title = handle_video_descriptions.get_video_title_db(video_id)
				progress.console.print(f"\[{str(video_id)}]: {str(db_video_title)}", highlight=False)
				
				# reset the youtube object
				youtube = ""
				try:
					video_comments(video_id,last_date_check_utc)
				except Exception:
					traceback.print_exc()
					video_id_errors.append(video_id)
					if (len(video_id_errors) > 5):
						print("5 failures occured, aborting")
						exit()
				progress.advance(task)

	if (len(video_id_with_new) > 0):
		print("\n------------------------------------")
		print("Videos with new comments or replies:")
		print_id_with_urL(video_id_with_new)
		print("\n")

	if (len(video_id_errors) > 0):
		print("\n----------------")
		print("ERROR WITH THESE:")
		print_id_with_urL(video_id_errors)
		print("\n")

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