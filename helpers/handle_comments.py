from googleapiclient.discovery import build
from os import path, getenv
try:
	import db_ops as db_ops
except:
	standalone = False

#from . import db_ops # moved to end to prevent import error when standalone

yt_api_key = getenv('YT_API_KEY')
db_verbose = True

# for progress display
new_comment_count = 0
update_comment_count = 0 

# temp video id(s)
video_id = 'UHwyHcvvem0'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw'
#video_id = 'gFCD4s_hsb4' # Mega IIe
#video_id = 'bqdyve-hhZY' # si vs sic

#video_id = 'UHwyHcvvem0,WQi8g1EBGIw,b6jih4osvxQ,JjY1lnMauVc,dbGohcv6uxo,bqdyve-hhZY,gFCD4s_hsb4'

# todo: remove this before deploy
verbose = False

# https://developers.google.com/youtube/v3/docs/commentThreads

# TODO: need to handle integers better
commentThread_mapping = {
	"id" : "yt_id",
	"etag" : "yt_etag",
	"snippet" : {
		"channelId" : "yt_snippet_channelId",
		"videoId" : "yt_snippet_videoId",
		#"topLevelComment": "yt_snippet_topLevelComment_Id", # doesn't exist how I want it to
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
		"channelId": "yt_snippet_channelId",
		"textDisplay": "yt_snippet_textDisplay",
		"textOriginal": "yt_snippet_textOriginal",
		"parentId": "yt_snippet_parentId",
		"canRate": "yt_snippet_canRate",
		"viewerRating": "yt_snippet_viewerRating",
		"likeCount": "yt_snippet_likeCount",
		#"moderationStatus": "yt_snippet_moderationStatus",
		"publishedAt": "yt_snippet_publishedAt",
		"updatedAt": "yt_snippet_updatedAt",
	},
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

def handle_comments(comments, timestamp, debug=False):
	if (debug): print("...[Handling a MULTIPLE comments]...")
	for comment in comments:
		handle_one_comment(comment, timestamp, debug=debug)

def handle_one_comment(comment, timestamp, debug=False):
	global time_at_launch_gmt
	global new_comment_count
	global update_comment_count

	if (debug): print("...[Handling a SINGLE comments]...")

	# TODO: need to check if comment exists and if it needs updating.
	sub_sql_columns = []
	sub_sql_values = []

	# outer level details of a comment object
	comment_id = comment['id']
	# child comments come with the parent id
	if (comment_id.find('.') != -1):
		(parent,child) = comment_id.split('.')
		comment_id = child

	# does comment exist?
	if (db_ops.does_comment_exist(comment_id, active=True, debug=False) == False):
		# let's go through the effort of adding!
		sub_sql_columns.append('yt_id')
		sub_sql_values.append(comment_id)

		comment_etag = comment['etag']
		sub_sql_columns.append('yt_etag')
		sub_sql_values.append(comment_etag)

		# handle snippet object of comment
		for sub_key in comment_mapping['snippet']:
			try:
				if (debug): print(f"Processing {sub_key}")
				if (sub_key == 'authorChannelId'):
					db_column = comment_mapping['snippet']['authorChannelId']
					db_value = comment['snippet']['authorChannelId']['value']
				else:
					db_column = comment_mapping['snippet'][sub_key]
					db_value = comment['snippet'][sub_key]
				sub_sql_columns.append(db_column)
				sub_sql_values.append(db_value)						
			except Exception as e:
				if (debug): print(f"*** Failed on {sub_key}.\n{e}\n")

		sub_sql_columns.append("last_update")
		sub_sql_values.append(timestamp)
		if (db_ops.db_insert_row("yt_comments", sub_sql_columns, sub_sql_values, timestamp=False)):
			#print(f"\t\tnew comment count: {new_comment_count}")
			new_comment_count = new_comment_count + 1
			if (debug): print("!!! DONE with handle_comments")
			return
		else:
			print("*** comment insert failed:")
			if (debug): print(f"\tsql_columns: {sub_sql_columns}")
			if (debug): print(f"\tsql_values: {sub_sql_values}")
	else:
		# comment does exist, so what do we update
		# TODO: Update like count

		# 1. get the last updatedAt date in our database table
		db_id = db_ops.get_latest_comment_db_id(comment_id)
		db_yt_updatedAt = db_ops.get_yt_comment_updatedAt(db_id)
		json_yt_updatedAt = comment['snippet']['updatedAt']
		#print(f"comment: [{comment_id}] last updated on yt: [{db_yt_updatedAt}], current value is: [{json_yt_updatedAt}]")
		# 2. compare to value in json
		if (db_yt_updatedAt != json_yt_updatedAt):
			# 3. if different then deactivate old comment and add new one
			db_ops.set_comment_active(db_id, False, timestamp)
			# 4. update whatever else
			#print("!!! TBD: need to update the comment")
			update_comment_count = update_comment_count + 1
			handle_one_comment(comment, timestamp, debug=False) # recurison should be okay... right?
			new_comment_count = new_comment_count - 1 # don't double dip!
	return # handle_one_comment()



def update_topLevelComment(item, timestamp, debug=False):
	# update the top Level table and then go find new replies
	commentThread_id = item['id']
	etag_id = item['etag']
	topLevelComment_id = item['snippet']['topLevelComment']['id']
	replycount = int(item['snippet']['totalReplyCount'])

	sql = f"UPDATE yt_commentThreads SET yt_snippet_totalReplyCount={replycount} WHERE yt_id='{topLevelComment_id}'"
	#def db_update_row(table, id_col, id_val, cols, vals, timestamp="True"):
	try:
		db_ops.db_update_row('yt_commentThreads', 'yt_id', topLevelComment_id, ['yt_snippet_totalReplyCount'], [replycount], timestamp)
	except:
		print("!!! Failed to update replycount")
		return False

	handle_replies(item, timestamp, debug)
	return True

def handle_replies(item, timestamp, debug=False):
	if (item['snippet']['totalReplyCount'] > 0):
		if (debug): print("+ Gathering commentThread_mapping")
		try:
			# does this response contain replies?
			if (isinstance(item['replies'], dict)):
				handle_comments(item['replies']['comments'], timestamp)
		except Exception as e:		
			if (debug): print("!!! Failed to find replies obj")
			if (debug): print(e)
			return False
	else:
		if (debug): print("+ No replies to this comment")


def prep_comment_for_db(item, timestamp, debug=False):
	sql_columns = []
	sql_values = []

	#! Step Number One
	# get top level id information
	commentThread_id = item['id']
	etag_id = item['etag']
	topLevelComment_id = item['snippet']['topLevelComment']['id']
	replycount = item['snippet']['totalReplyCount']

	if (debug): print(f"\t commentThread_id = [{commentThread_id}]")
	sql_columns.append("yt_id")
	sql_values.append(commentThread_id)
	#
	if (debug): print(f"\t etag_id = [{etag_id}]")
	sql_columns.append("yt_etag")
	sql_values.append(etag_id)
	# I think this will link the top level comment to the comment id in the comments table
	if (debug): print(f"\t topLevelComment_id = [{topLevelComment_id}]")
	sql_columns.append("yt_snippet_topLevelComment_id")
	sql_values.append(topLevelComment_id)
	#
	if (debug): print(f"\t replycount = [{replycount}]")
	
	#! Step Number Two
	# prep the snippet section
	if (debug): print("\n+ Gathering snippet information")
	for snippet_key in item['snippet']:
		if (debug): print(f"{snippet_key}: {item['snippet'][snippet_key]}")
		
		# loop through the yt response and match up to sql columns
		if isinstance(item['snippet'][snippet_key], dict):
			# toplevelComment is a dict and contains a comment
			if (debug): print(f"+ Got dict: {snippet_key}")
			handle_one_comment(item['snippet']['topLevelComment'], timestamp)
		else:
			yt_snippet_key = snippet_key # probably not needed, but I did it before, I guess
			db_column = commentThread_mapping['snippet'][snippet_key]
			if (snippet_key.lower() == 'totalreplycount'):
				db_value = int(item['snippet'][snippet_key])
			else:
				db_value = item['snippet'][snippet_key]
			if (debug): print(f"\t column: {db_column}")
			sql_columns.append(db_column)
			if (debug): print(f"\t value:  {db_value}")
			sql_values.append(db_value)

	# TODO: Need to add timestamp
	# TODO: check to see if thread already exists and needs an update

	sql_columns.append('last_update')
	sql_values.append(timestamp)

	if (db_ops.db_insert_row("yt_commentThreads", sql_columns, sql_values, timestamp=False) == False):
		print("!!! insert into yt_commentThreads failed")
		print("\t===")
		print(sql_columns)
		print("\t---")
		print(sql_values)
		print("\t===")

	#! Step Number Three
	handle_replies(item, timestamp, debug)

	if (debug): print("+ DONE with topLevelComments\n-----------------\n\n")
	return True

def video_comments(video_id, timestamp, debug=False):
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
				if (debug): print(f"\n+ For video [{video_id}], found [{comment_id}] aready EXISTS in db")
				db_replyCount = db_ops.get_replyCount(comment_id)
				if (replycount != db_replyCount):
					if (update_topLevelComment(item, timestamp) == False):
						# update the reply count in the topLevelComment table
						# and process replies
						printf(f"!!! update failed for [{comment_id}]")
				# else:
				# 	# just process replies (looking for comments that changed)
				handle_replies(item, timestamp, debug)

			else:
				if (debug): print(f"+ For video [{video_id}], [{comment_id}] is new, attempting ADD")
				# this is a new comment, need to add to db
				if(prep_comment_for_db(item, timestamp) == False):
					print(f"!!! db insert fail for [{comment_id}]")

		# Again repeat
		if 'nextPageToken' in video_response:
			video_response = youtube.commentThreads().list(
					part = 'snippet,replies',
					videoId = video_id,
					pageToken = video_response['nextPageToken']
				).execute()
		else:
		 	break




def main():
	#print(f"Did you mean to run {path.basename(__file__)} standalone?")
	global video_id
	
	# todo disable this stuff for later.

	if (db_ops.create_connection() == False): exit()

	# for testing, use these values
	from datetime import datetime
	from pytz import timezone,utc
	time_at_launch = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S") # used later, get the time asap
	time_at_launch_gmt = utc.localize(datetime.strptime(time_at_launch, "%Y-%m-%d %H:%M:%S")) # adds +00:00

	# todo replace with actual string
	video_ids = video_id
	for video_id in video_ids.split(","):
		video_comments(video_id, time_at_launch_gmt, debug=False)

	exit()

if __name__ == '__main__':
	main()

from . import db_ops


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