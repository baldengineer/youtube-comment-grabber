from googleapiclient.discovery import build
from os import path, getenv
#from . import db_ops # moved to end to prevent import error when standalone

yt_api_key = getenv('YT_API_KEY')
db_verbose = True

# temp video id(s)
video_id = 'UHwyHcvvem0'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw'
#video_id = 'UHwyHcvvem0,WQi8g1EBGIw,b6jih4osvxQ,JjY1lnMauVc,dbGohcv6uxo,bqdyve-hhZY'

# Todo: Add etag to database
# Todo: should topLevelComment be an id
#       so that it links to a comment in the comment table?

# https://developers.google.com/youtube/v3/docs/commentThreads
commentThread_mapping = {
	"id" : "yt_id",
	"etag" : "yt_etag",
	"snippet" : {
		"channelId" : "yt_snippet_channleId",
		"videoId" : "yt_snippet_videoId",
		"topLevelComment": "yt_snippet_topLevelComment",
		"canReply": "yt_snippet_canReply",
		"totalReplyCount" : "yt_snippet_totalReplayCount",
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

def handle_mixed_vals(val):
	# oh youtube, you give us too many options
	if (isinstance(val,list)):
		new_value  = ",".join(val)
	elif (val.isnumeric()):
		new_value = int(val)
	else:
		new_value = val
	return new_value

def update_comments(time_at_launch_gmt):
	print("shrug")
	return

def main():
	#print(f"Did you mean to run {path.basename(__file__)} standalone?")
	update_comments("nothing")
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