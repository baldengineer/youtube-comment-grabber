from googleapiclient.discovery import build
from os import path
import json



#! youtube video id details:
# Exactly 11 characters
# Allowed symbols: a-z, A-Z, 0-9, -, and _
# Remember, it can start with a - or _, so test those

##########################################
def load_video_ids(text_file_with_ids, verbose=False):
	video_ids = []
	try:
		with open(text_file_with_ids, 'r') as file:
			print(f"Loading video ids from {text_file_with_ids}")
			line_number = 1
			for line in file:
				#print(line, end='')  # Print each line without adding an extra newline
				# ignore comments
				clean_line = line.strip()
				if (clean_line == ""):
					#print(f"Blank line at {line_number}")
					continue
				if (clean_line.startswith("#")):
					if (verbose): print(f"Line {line_number}: Skipping {clean_line}")
					continue
				video_ids.append(clean_line)
				line_number = line_number + 1

	except FileNotFoundError:
		print(f"The file '{text_file_with_ids}' was not found.")
		exit()
	except Exception as e:
		print(f"An error occurred: {e}")
		exit()

	print(f"Loaded {len(video_ids)} ids, first id is: {video_ids[0]}")
	# TODO: Need to make this a command line option
	video_ids.reverse()

	# sql stuff
	for id in video_ids:
		#sql = f"INSERT INTO yt_videos (yt_id) VALS ('{id}')"
		if (db_ops.db_insert_row('yt_videos',['yt_id','active_update'],[id,1],False) ==  False):
			exit()
	return video_ids

##########################################
def main():
	# import sekrits
	# yt_api_key = sekrits.yt_api_key
	print(f"Did you mean to run {path.basename(__file__)} standalone?")
	exit()
	global text_file_with_ids
	# so the code works if testing this module standalone
	text_file_with_ids = f"../{text_file_with_ids}"
	#load_video_ids()
	#save_json_string(yt_api_key, printing=True, file="five-results.json")
	#open_json_string()

	test_all_threads(yt_api_key)

if __name__ == '__main__':
	main()

from . import db_ops
