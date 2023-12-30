from googleapiclient.discovery import build
from os import path, getenv
import db_ops as db_ops
#from . import db_ops # moved to end to prevent import error when standalone

yt_api_key = getenv('YT_API_KEY')
db_verbose = True

# temp video id(s)
#video_id = 'UHwyHcvvem0'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw'
video_id = 'UHwyHcvvem0,WQi8g1EBGIw,b6jih4osvxQ,JjY1lnMauVc,dbGohcv6uxo,bqdyve-hhZY'

# todo: remove this before deploy

verbose = True
# Todo: should topLevelComment be an id
#       so that it links to a comment in the comment table?

# https://developers.google.com/youtube/v3/docs/commentThreads
commentThread_mapping = {
	"id" : "yt_id",
	"etag" : "yt_etag",
	"snippet" : {
		"channelId" : "yt_snippet_channelId",
		"videoId" : "yt_snippet_videoId",
		"topLevelComment": "yt_snippet_topLevelComment",
		"canReply": "yt_snippet_canReply",
		"totalReplyCount" : "yt_snippet_totalReplyCount",
		"isPublic" : "yt_snippet_isPublic",
	},
	"replies" :{
		"comments" : "yt_replies_comments",

	},
}

# TODO: authorChannelId is nested from the API
# https://developers.google.com/youtube/v3/docs/comments
comment_mapping = {
	"id" : "yt_id",
	"etag" : "yt_etag",
	"snippet" : {
		"authorDisplayName": "yt_snippet_authorDisplayName",
		"authorProfileImageUrl": "yt_snippet_authorProfileImageUrl",
		"authorChannelUrl": "yt_snippet_authorChannelUrl",
		"authorChannelId": 	"yt_snippet_authorChannelId",
	},
	"channelId": "yt_channelId",
	"textDisplay": "yt_textDisplay",
	"textOriginal": "yt_textOriginal",
	"parentId": "yt_parentId",
	"canRate": "yt_canRate",
	"viewerRating": "yt_viewerRating",
	"likeCount": "yt_likeCount",
	"moderationStatus": "yt_moderationStatus",
	"publishedAt": "yt_publishedAt",
	"updatedAt": "yt_updatedAt",
}

# TODO: started as same function in handle_video_desc, now updated.
def handle_mixed_vals(val):
	# oh youtube, you give us too many options
	#print(f"\t\t{val} = {type(val)}")
	if (isinstance(val,list)):
		new_value  = ",".join(val)
	elif (isinstance(val,int)):
		# i guess bool is an int? lol
		if (isinstance(val,bool)):
			if (val):
				new_value = "True"
			else:
				new_value = "False"
		else:
			new_value = int(val)
	else:
		new_value = val
	return new_value

# dude, you already pull the comments in the main py. 
# why you re-writing it silly?
def prep_comment_for_db(item, debug=False):
	sql_columns = []
	sql_values = []

	comment_id = item['snippet']['topLevelComment']['id']
	replycount = item['snippet']['totalReplyCount']

	if (debug): print(f"comment_id = [{comment_id}]")
	if (debug): print(f"replycount = [{replycount}]")
	sql_columns.append("yt_snippet_topLevelComment_id")
	sql_values.append(comment_id)

	for obj_key in commentThread_mapping.keys():
		# if the obj_key is a str, then it is "top level" in the json structure
		if (isinstance(commentThread_mapping[obj_key], str)):
			# top level key like thread
			try:
				yt_resp_key = obj_key
				db_column = commentThread_mapping[obj_key]
				db_value = item[obj_key]
				if (debug): print("---")
				if (debug): print(f"column: {db_column}")
				sql_columns.append(db_column)
				if (debug): print(f"value:  {db_value}")
				sql_values.append(db_value)
			except Exception as e:
				if (debug): print(f"Failed on{obj_key}.\n{e}")
		# if it is a dict, then it contains other objs, like snippet and replies
		elif (isinstance(commentThread_mapping[obj_key], dict)):
			if (debug): print(f"trying: [{obj_key}]")
			if (obj_key == "replies"): continue
			#if (obj_key == "topLevelComment"): continue
			try:
				sub_level = commentThread_mapping[obj_key]
				for sub_key in sub_level.keys():
					if (sub_key == "topLevelComment"): continue
					yt_resp_key = obj_key
					db_column = commentThread_mapping[obj_key][sub_key]
					db_value = item[obj_key][sub_key]
					if (debug): print(f"\tsub_column: {db_column}")
					sql_columns.append(db_column)
					if (debug): print(f"\tsub_value:  {handle_mixed_vals(db_value)}")
					sql_values.append(handle_mixed_vals(db_value))
			except Exception as e:
				print(f"WARNING: Failed (probably missing in response) on {obj_key}/{sub_level}.\n{e}\n")
		else:
			print(f"unknown: {type(commentThread_mapping[obj_key])}")

	if (debug): print(f"\n\n\ncols: {sql_columns}\n-\nvals: {sql_values}")				
	try:
		db_ops.db_insert_row("yt_commentThreads", sql_columns, sql_values, timestamp=False)
		return True
	except Exception as e:
		print(f"insert failed\n{e}\n")
		return False

def video_comments(video_id, last_date_check_utc, verbose=verbose):
	global video_id_with_new
	global video_id_counter

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

			# is the id in our database?
			if (db_ops.does_topLevelComment_exist(comment_id)):
				# it exists so we need to see if it has been updated
				print(f"Found [{comment_id}] in database")
			else:
				print(f"db does not have [{comment_id}]")
				# this is a new comment, need to add to db
				if(prep_comment_for_db(item) == False):
					print(f"db insert fail for [{comment_id}]")

			break

			
			

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



def main():
	#print(f"Did you mean to run {path.basename(__file__)} standalone?")
	global video_id
	# todo disable this stuff for later.

	if (db_ops.create_connection() == False): exit()

	# todo replace with actual string
	video_ids = video_id
	#video_comments(video_id,"gmt string",verbose=True)
	for video_id in video_ids.split(","):
		video_comments(video_id,"gmt string",verbose=True)

	exit()

if __name__ == '__main__':
	main()

from . import db_ops


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