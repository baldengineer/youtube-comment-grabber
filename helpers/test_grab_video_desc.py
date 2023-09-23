from googleapiclient.discovery import build

from os import path, getenv

yt_api_key = getenv('YT_API_KEY')

# temp video id
video_id = 'UHwyHcvvem0,WQi8g1EBGIw'

# creating youtube resource object
youtube = build('youtube', 'v3', developerKey=yt_api_key)

# retrieve youtube video results
video_response=youtube.videos().list(
part='snippet',
id=video_id
).execute()

#print(video_response)

#exit()
while video_response:

	# extracting required info
	# from each result object
	for item in video_response['items']:
		# moderationStatus requires authorization (e.g. channel owner)
		# Extacting comments

		# top level things
		#comment_id = item['snippet']['topLevelComment']['id']
		#replycount = item['snippet']['totalReplyCount']
		yt_title = item['snippet']['title']
		yt_publishedAt = item['snippet']['publishedAt']
		print(f"'{yt_title}'\nPublished: {yt_publishedAt}")
	
	if 'nextPageToken' in video_response:
		video_response = youtube.commentThreads().list(
				part = 'snippet,replies',
				videoId = video_id,
				pageToken = video_response['nextPageToken']
			).execute()
	else:
		break