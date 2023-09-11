![early screenshot](images/early_screenshot.png)
# youtube-comment-grabber
You probably don't want to use this tool yet. This code is pretty rough and not the direction I want to go anyway. But it might accidentally be helpful if you want to see examples of interacting with the YouTube API.

The purpose of the tool is to help find when people reply to videos on channels you do not own. Eventually, you'll be able to reply directly from the tool.

# First-time usage
You need to do the things in "Things you need" first. In short, you'll need to do the following:
1. Create a `.env` file in the same directory as `youtube_comment_grabber.py`. (`.env_sample` is provided0
2. In `.env` set your YouTube API and your local time zone. ([Here is a list of supported ptyz timezones](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568))
3. Create (or edit) `last_check.txt`. This has the date in `YYYY-MM-DD HH:MM:SS` format to compare against. The script converts that time from your set timezone to GMT!
4. Edit `video_ids.txt` to contain at least 1 video id you want to check.


# Usage
When you want to check for new comments, run `python youtube_comment_grabber.py`. It will check each video id and its comments for anything posted since the last time the script ran. 

The script places the current date and time in a file called `last_check.txt`. Edit that date if you want to change the compare. 

(Yeah, I know, this is messy. I have something better coming.)

There isn't much in the way of error checking, so do not be surprised if the script just fails. 

## Command Line Options
Super basic commandline checks. Please use the same case for `noup`
* `-q` is a quiet mode. You'll only get status updates and a list of URLs with new comments (or replies.)
* `-noup` does not update the `last_check.txt`. (Good if you're testing video_ids or something)
* `-h  lists these three amazing options`


## YouTube API Usage Note
By default, you get 10,000 API requests per day quota. When this script runs, each video id it checks incurs a 1 quote cost. Google provides an [API quota dashboard](https://console.cloud.google.com/iam-admin/quotas), which you can access in the cloud console. More information is [available here](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits) as well.

The next version of the script will cache comments and be smarter about which videos it checks. But even if you're tracking 100 videos, you can basically check them 3 times a day and still be under the limit. (It'll also track how many queries it is doing.)

Currently, this script does not do any create actions. It is read-only.


# Things you need
You need an API key from Google, some Python Modules, and a list of YouTube video IDs.

## Get YouTube Data API v3
First, you'll need a Google API Key. There are many tutorials available on this process, but here are the are the basic steps:

1. Log in to [Google Developers Console](https://console.cloud.google.com/apis/dashboard).
2. Create a new project.
3. On the new project dashboard, click Explore & Enable APIs.
4. In the library, navigate to **YouTube Data API v3** under YouTube APIs.
5. Enable the API.
6. Create a credential.

Creating the credential
1. On the left side, go to **Credentials**
2. Top of the screen click **+ Create Credentials** and select **API Key**
3. After a few seconds, you'll see an API key. Save that.

(Optionally, you can edit restrictions and limit the scope to the YouTube Data API v3.)

Save that key in a file called `.env` as:
`YT_DATA_API = 'key goes here`

## Python Modules
I'm working on transitioning this project to a venv. Until then, you'll need to install a few packages manually. 

Packages needed are:
```pip install google-api-python-client pytz python-dotenv```

All are available with `pip`. 

## YouTube Video IDs
The file `video_ids.txt` should contain a list of the IDs to check. One per line. You can use `#` as a comment. I'd suggest starting with 1 - 5

The video id appears at the end of the full video URL. For example:
```https://www.youtube.com/watch?v=bqdyve-hhZY```
The video id is: `bqdyve-hhZY`.

The 

