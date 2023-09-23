from googleapiclient.discovery import build
from os import path, getenv
import db_ops

yt_api_key = getenv('YT_API_KEY')
db_verbose = True

# temp video id(s)
video_id = 'UHwyHcvvem0'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw'


# skipping dislikeCount because it isn't returned at all 
# unless you are an authorized user of the channel
video_desc_mapping = {
	"id" : "yt_id",
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
		#"dislikeCount" : "yt_statistics.dislikeCount",
		"commentCount" : "yt_statistics.commentCount",
	}
}

# creating youtube resource object
youtube = build('youtube', 'v3', developerKey=yt_api_key)

# retrieve youtube video results
video_response=youtube.videos().list(
part='snippet,contentDetails,statistics',
id=video_id
).execute()

#print(video_response)

#exit()

def build_sql_column_list(key_list, obj_array, mapping):
	skipped = []
	for key in key_list:
		# we don't care about some of the values we got back	
		try:
			print(f"{key} = {mapping[obj_array][key]}")
		except:
			skipped.append(key)

	print("\nSkipped these")
	for skip in skipped:
		print(skip)


	return
while video_response:
	# extracting required info
	# from each result object
	#key_list = list(video_response['items'].keys())

	# top_key_list = list(video_response.keys())
	#print(f"top keys: {top_key_list}")

	# what are the youtube videos we need to map to database later
	# items = video_response['items'][0]
	# snippet_key_list = list(items['snippet'].keys())
	# contentDetails_key_list = list(items['contentDetails'].keys())
	# statistics_key_list = list(items['statistics'].keys())
	# print(f"snippet keys: {snippet_key_list}")
	# build_sql_column_list(snippet_key_list, "snippet", video_desc_mapping)
	# print(f"\ncontentDetails keys: {contentDetails_key_list}")
	# build_sql_column_list(contentDetails_key_list, "contentDetails", video_desc_mapping)
	# print(f"\nstatistics keys: {statistics_key_list}")
	# build_sql_column_list(statistics_key_list, "statistics", video_desc_mapping)


	# start building the sql query
	for item in video_response['items']:
		sql_columns = []
		sql_values = []
		
		yt_id = item['id']
		yt_title = item['snippet']['title']
		print(f"Processing [{yt_id}]: {yt_title}")
		
		#print(f"#########\n{video_desc_mapping.keys()}\n#########")
		for obj_key in video_desc_mapping.keys():
			if (isinstance(video_desc_mapping[obj_key], str)):
				# top level key like id and title
				#print(f"string: {video_desc_mapping[obj_key]}")
				try:
					yt_resp_key = obj_key
					db_column = video_desc_mapping[obj_key]
					db_value = item[obj_key]
					sql_columns.append(db_column)
					sql_values.append(db_value)
					#if (db_verbose): print(f"[top] obj_key: {obj_key}, db_column: {db_column}, db_value: {db_value}")
					if (db_verbose): print(f"[top] obj_key: {obj_key}, db_column: {db_column}")
				except Exception as e:
					print(f"Failed on {obj_key}.\n{e}")
			elif (isinstance(video_desc_mapping[obj_key], dict)): 
				try:
					sub_level = video_desc_mapping[obj_key]
					for sub_key in sub_level.keys():
						yt_resp_key = obj_key
						db_column = video_desc_mapping[obj_key][sub_key]
						db_value = item[obj_key][sub_key]
						sql_columns.append(db_column)
						sql_values.append(db_value)
						#if (db_verbose): print(f"obj_key: {obj_key}, sub_key: {sub_key}, db_column: {db_column}, db_value: {db_value}")
						if (db_verbose): print(f"obj_key: {obj_key}, sub_key: {sub_key}, db_column: {db_column}")
				except Exception as e:
						print(f"Failed on {obj_key}/{sub_level}.\n{e}")
			else:
				print(f"unknown: {type(video_desc_mapping[obj_key])}")
		print(f"\n\n\ncols:{sql_columns}")
		print(f"\nvals:{sql_values}")
	# keep refreshing video_response object if there are more pages to grab 
	# we only get like 50 results at a time (depends on the call)
	if 'nextPageToken' in video_response:
		if (db_verbose): print("### Fetching next page from YouTube API")
		video_response = youtube.commentThreads().list(
				part = 'snippet,replies',
				videoId = video_id,
				pageToken = video_response['nextPageToken']
			).execute()
	else:
		break