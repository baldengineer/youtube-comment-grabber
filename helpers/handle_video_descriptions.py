from googleapiclient.discovery import build
from os import path, getenv
from rich.progress import (
	Progress,
	TextColumn,
	BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

#from . import db_ops # moved to end to prevent import error when standalone

yt_api_key = getenv('YT_API_KEY')
db_verbose = False

# temp video id(s)
#video_id = 'UHwyHcvvem0'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw,b6jih4osvxQ,JjY1lnMauVc,dbGohcv6uxo,bqdyve-hhZY'


# skipping dislikeCount because it isn't returned at all 
# unless you are an authorized user of the channel
video_desc_mapping = {
	"id" : "yt_id",
	"snippet" : {
		"publishedAt" : "yt_snippet_publishedAt",
		"title" : "yt_snippet_title",
		"channelId" : "yt_snippet_channelId",
		"description" : "yt_snippet_description",
		"channelTitle" : "yt_snippet_channelTitle",
		#"tags" : "yt_snippet_tags",
		"categoryId" : "yt_snippet_categoryId",
		"liveBroadcastContent" : "yt_snippet_liveBroadcastContent",
	},
	"contentDetails" : {
		"duration" : "yt_details_duration",
	},
	"statistics" : {
		"viewCount" : "yt_statistics_viewCount",
		"likeCount" : "yt_statistics_likeCount",
		#"dislikeCount" : "yt_statistics_dislikeCount",
		"commentCount" : "yt_statistics_commentCount",
	}
}

def handle_mixed_vals(val):
	# oh youtube, you give us too many options
	if (isinstance(val,list)):
		new_value  = ",".join(val)
	elif (val.isnumeric()):
		new_value = int(val)
	else:
		new_value = val
	return new_value

def update_video_descriptions(time_at_launch_gmt, debug=False):
	if (debug): print("Fetching video ids from db...")
	video_id_list = db_ops.db_get_video_ids()

	progress = Progress(
    	TextColumn("[progress.description]{task.description}"),
    	BarColumn(),
    	TaskProgressColumn(),
    	TextColumn("[bold blue]{task.fields[vid]}")
	)

	#with Progress() as progress:
	with progress:
		vid = "..."
		task = progress.add_task("Updating descriptions", vid=vid, total=len(video_id_list))
		# chunk the ids in groups of 50
		for index in range(0, len(video_id_list), 50):
			#print(video_id_list[index: index + 50])
			partial_video_id_list = video_id_list[index: index + 50]
			video_ids = ",".join(partial_video_id_list)

			if (debug): print(f"Processing records {index} to {index+len(partial_video_id_list)}...")
			# creating youtube resource object
			youtube = build('youtube', 'v3', developerKey=yt_api_key)

			# retrieve youtube video results
			video_response=youtube.videos().list(
			part='snippet,contentDetails,statistics',
			id=video_ids
			).execute()
			#print(video_response)
			while video_response:
				# extracting required info
				# from each result object

				# start building the sql query
				for item in video_response['items']:
					sql_columns = []
					sql_values = []
					
					yt_id = item['id']
					yt_title = item['snippet']['title']
					if (debug): progress.console.print(f"\[{str(yt_id)}]: {str(yt_title)}", highlight=False)
					#task.fields['desc'] = str(yt_title)
					progress.update(task, vid=yt_title)
					#if (debug): print(f"Updating [{yt_id}]: {yt_title}", flush=True)
					#db_ops.does_videoid_exist(yt_id) # switched to update, but only if ID is in the table
					
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
								sql_values.append(handle_mixed_vals(db_value))
								#if (db_verbose): print(f"[top] obj_key: {obj_key}, db_column: {db_column}, db_value: {db_value}")
								if (db_verbose): print(f"[top] obj_key: {obj_key}, db_column: {db_column}")
							except Exception as e:
								print(f"!!! Failed on {obj_key}.\n{e}")
						elif (isinstance(video_desc_mapping[obj_key], dict)): 
							try:
								sub_level = video_desc_mapping[obj_key]
								for sub_key in sub_level.keys():
									yt_resp_key = obj_key
									db_column = video_desc_mapping[obj_key][sub_key]
									db_value = item[obj_key][sub_key]
									sql_columns.append(db_column)
									sql_values.append(handle_mixed_vals(db_value))
									#if (db_verbose): print(f"obj_key: {obj_key}, sub_key: {sub_key}, db_column: {db_column}, db_value: {db_value}")
									if (db_verbose): print(f"obj_key: {obj_key}, sub_key: {sub_key}, db_column: {db_column}")
							except Exception as e:
									print(f"WARNING: Failed (probably missing in response) on {obj_key}/{sub_level}.\n{e}")
						else:
							print(f"!!! unknown: {type(video_desc_mapping[obj_key])}")
					#print(f"\n\n\ncols:{sql_columns}")
					#print(f"\nvals:{sql_values}")
					#db_ops.db_insert_row("yt_videos",sql_columns,sql_values)
					db_ops.db_update_row("yt_videos","yt_id",yt_id,sql_columns,sql_values,time_at_launch_gmt)

					progress.advance(task)


				# keep refreshing video_response object if there are more pages to grab 
				# we only get like 50 results at a time (depends on the call)
				if 'nextPageToken' in video_response:
					if (db_verbose): print("### Fetching next page from YouTube API")
					video_response=youtube.videos().list(
							part='snippet,contentDetails,statistics',
							id=video_ids,
							pageToken = video_response['nextPageToken']
						).execute()
				else:
					break
	return

def get_video_title_db(video_id):
	sql = "SELECT yt_snippet_title FROM yt_videos WHERE yt_id = ?"
	result = db_ops.db_get_single_element(sql, video_id)
	if (result is None): return ""
	return result



def main():
	print(f"Did you mean to run {path.basename(__file__)} standalone?")
	exit()

if __name__ == '__main__':
	main()

from . import db_ops