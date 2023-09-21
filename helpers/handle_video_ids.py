from googleapiclient.discovery import build
from os import path
import json

text_file_with_ids = path.join("data","video_ids.txt")

#! youtube video id details:
# Exactly 11 characters
# Allowed symbols: a-z, A-Z, 0-9, -, and _
# Remember, it can start with a - or _, so test those


##########################################
#? I don't know how to handle this from a module....yet :)

def yt_api_query(video_id, yt_api_key):
	global youtube
	print("I decided not to do this...")
	exit()
	# empty list for storing reply
	#print(f"Handling: https://www.youtube.com/watch?v={video_id}")

	# creating youtube resource object
	youtube = build('youtube', 'v3', developerKey=yt_api_key)

	# retrieve youtube video results
	video_response=youtube.commentThreads().list(
		part='snippet,replies',
		videoId=video_id
		).execute()

	return video_response


##########################################
def open_json_string(file='sample.json'):
	print("------ RUNNING OFFLINE ------")
	print(f"Loading results from {file}...", end='')
	with open(file, 'r') as infile:
		results = json.load(infile)
	print("done!")
	return results


##########################################
def save_json_string(yt_api_key, printing=False, file='sample.json'):
	video_ids = load_video_ids()

	if (len(video_ids) > 0):
		video_ids_json = json.dumps(video_ids[0])
	else:
		print("Did not load any ids?")
		exit()

#	exit()
	results = yt_api_query(video_ids, yt_api_key)

	print(f"Saving results to {file}...", end='')
	with open(file,"w") as outfile:
		json.dump(results,outfile)
	print("done!")
	if (printing):
		print(json.dumps(results, indent=2))


##########################################
def load_video_ids(verbose=False):
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
	return video_ids

##########################################
def test_all_threads(yt_api_key):
	print("Nope. Not doing it")
	return

	youtube = build('youtube', 'v3', developerKey=yt_api_key)

	response = youtube.commentThreads().list(
		part='snippet,replies',
		allThreadsRelatedToChannelId=''
		).execute()
	print(response)
	json.dumps(response)

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

