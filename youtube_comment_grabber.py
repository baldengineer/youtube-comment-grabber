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
from helpers import handle_comments
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

def print_id_with_urL(video_ids):
	for video_id in video_ids:
		print(f"https://youtube.com/watch?v={video_id}")

def main():
	global youtube
	
	# bail if we can't open the db
	if (db_ops.create_connection() == False): exit()

	# update video descriptions in yt_videos
	handle_video_descriptions.update_video_descriptions(time_at_launch_gmt)

	# TODO: Need to check if comments changed!
	# get video_ids for updating comments
	video_ids = db_ops.db_get_video_ids(True)
	video_id_errors = 0 # failsafe

	if (len(video_ids) > 0):
		with Progress() as progress:
			task = progress.add_task("Checking for comments", total=len(video_ids))
			for video_id in video_ids:
				# give pretty update status
				db_video_title = handle_video_descriptions.get_video_title_db(video_id)F
				progress.console.print(f"\[{str(video_id)}]: {str(db_video_title)}", highlight=False)
				
				# reset the youtube object
				youtube = ""
				try:
					handle_comments.video_comments(video_id, time_at_launch_gmt, debug=False)
				except Exception:
					traceback.print_exc()
					video_id_errors.append(video_id)
					if (len(video_id_errors) > 5):
						print("5 failures occured, aborting")
						exit()
				progress.advance(task)

if __name__ == '__main__':
	main()



# Originally based this example:
# https://www.geeksforgeeks.org/how-to-extract-youtube-comments-using-youtube-api-python/
## although, I think only one API call is still from that example. (but check it out as a starting point)

# Copyright (c) 2023-2024 James Lewis (@baldengineer)

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