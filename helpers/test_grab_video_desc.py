from googleapiclient.discovery import build
from os import path, getenv

yt_api_key = getenv('YT_API_KEY')

# temp video id(s)
#video_id = 'UHwyHcvvem0'
video_id = 'UHwyHcvvem0,WQi8g1EBGIw'

video_desc_mapping = {
	"id" : "yt_id",
	"title" : "title",
	"snippet" : {
		"publishedAt" : "yt_snippet.publishedAt",
		"title" : "yt_snippet.title",
		"channelId" : "yt_snippet.channelId",
		"description" : "yt_snippet.description",
		"channelTitle" : "yt_snippet.channelTitle",
		"tags" : "yt_snippet.tags",
		"categoryId" : "yt_snippet.categoryId",
		"liveBroadcastContent" : "yt_snippet.liveBroadcastContent",
	},
	"contentDetails" : {
		"duration" : "yt_details.duration",
	},
	"statistics" : {
		"viewCount" : "yt_statistics.viewCount",
		"likeCount" : "yt_statistics.likeCount",
		"dislikeCount" : "yt_statistics.dislikeCount",
		"commentCount" : "yt_statistics.commentCount",
	}
}

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