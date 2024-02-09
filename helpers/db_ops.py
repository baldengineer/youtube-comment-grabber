import sqlite3
import datetime
from os import path, getenv


# Global for the database
db_conn = None
db_file = None

# Get the database file
try:
	db_file = path.join("data",getenv('db_file').strip())
except:
	db_file = path.join("data","yt_data.db")
	print(f"Failed to get database file from .env. Using default: {db_file}")
	
def create_connection(db_file=db_file):
	""" create a database connection to a SQLite database """
	global db_conn
	db_conn = None
	try:
		db_conn = sqlite3.connect(db_file)
		print(f"Connected to db. Sqlite ver: {sqlite3.version}")
		return True
	except Exception as e:
		print(f"DB connection failed:\n{e}")
		return False
	
def db_get_video_ids(acitve_only=True):
	if (acitve_only):
		sql = "SELECT yt_id FROM yt_videos WHERE active_update=1"
	else:
		sql = "SELECT yt_id FROM yt_videos"
	curr = db_conn.cursor()
	curr.execute(sql)
	rows = curr.fetchall()
	video_ids = []
	for row in rows:
		video_ids.append(row[0].strip())
	print(f"db has {len(video_ids)} video ids")
	return video_ids

def db_get_single_element(sql, vals=None): 
	curr = db_conn.cursor()
	if (vals == None):
		curr.execute(sql)
	if (isinstance(vals,str)):
		curr.execute(sql,[vals]) # need a list for vals
	if (isinstance(vals,tuple)):
		curr.execute(sql,vals)

	rows = curr.fetchall()
	if (len(rows) > 0): 
		if (isinstance(rows[0][0],int)):
			return f"{rows[0][0]}"
		else:
			if (rows[0][0] is None): return ""
			return rows[0][0].strip()
	else:
		return None

def get_database_schema_version():
	version = db_get_single_element("SELECT database_version FROM meta")
	print(f"Database schema ver: {version}")
	return version

def get_replyCount(comment_id):
	sql = f"select yt_snippet_totalReplyCount from yt_CommentThreads where yt_id='{comment_id}'"
	replyCount = int(db_get_single_element(sql))
	return replyCount

def get_last_db_update():
	last_db_update = db_get_single_element("SELECT last_db_update FROM meta")
	print(f"Last data dump: {last_db_update}")
	return last_db_update

def get_last_comment_check():
	last_comment_check = db_get_single_element("SELECT last_comment_check FROM meta")
	#print(f"Last data dump: {last_db_update}")
	if (last_comment_check is None) or (last_comment_check == ""):
		print("Need to set last_comment_check date in meta table")
		exit()
	return last_comment_check

def build_insert_list(cols):
	col_list = ""
	parameter_list = ""
	for col in cols:
		col_list = col_list + "," + col
		parameter_list = parameter_list + ",?"
	col_list = col_list[1:]
	parameter_list = parameter_list[1:]
	#print(f"columns: {col_list}")
	return (col_list, parameter_list)

def build_update_list(cols):
	col_list = "=?,".join(cols) +"=?"
	return (col_list)

def does_comment_exist(comment_id, active=True, debug=False):
	sql = f"SELECT count(yt_id) FROM yt_comments WHERE yt_id='{comment_id}' and active={int(active)}"
	match_count = db_get_single_element(sql)
	if (match_count.isnumeric()):
		if (int(match_count) > 0):
			if (debug): print(f"{comment_id} matched {match_count} rows")
			return True
		else:
			if (debug): print(f"{comment_id} matched 0 rows")
			return False
	else:
		print(f"ERROR: [does_comment_exist]: {comment_id} wasn't numeric, returning False")	
		return False

	# uh oh, this shouldn't happen
	return False

def does_topLevelComment_exist(topLevelCommentId, debug=False):
	sql = f"SELECT count(yt_id) FROM yt_commentThreads WHERE yt_id='{topLevelCommentId}'"
	match_count = db_get_single_element(sql)
	if (match_count.isnumeric()):
		if (int(match_count) > 0):
			if (debug): print(f"{topLevelCommentId} matched {match_count} rows")
			return True
		else:
			if (debug): print(f"{topLevelCommentId} matched 0 rows")
			return False
	else:
		print(f"ERROR: [does_topLevelComment_exist]: {topLevelCommentId} wasn't numeric, returning False")	
		return False

# why doesn't this function return anything?
def does_videoid_exist(video_id_raw):
	video_id = video_id_raw.strip()
	sql = f"SELECT count(yt_id) from yt_videos WHERE yt_id='{video_id}'"
	match_count = db_get_single_element(sql)
	if (match_count.isnumeric()):
		if (int(match_count) > 0):
			print(f"{video_id} matched {match_count} rows")
		else:
			print(f"{video_id} matched 0 rows, but you shouldn't see this...")
	else:
		print(f"{video_id} return type None")


# insert is failing because tags are an array! 
# gah
		
# TODO: Handle timestamps better
def db_update_row(table, id_col, id_val, cols, vals, timestamp="True"):
	if (timestamp != ""):
		cols.append('last_update')
		vals.append(timestamp)
	col_list = build_update_list(cols)
	
	sql = f"UPDATE {table} SET {col_list} WHERE {id_col}='{id_val}'"
	#print(f"update sql: {sql}")

	curr = db_conn.cursor()
	curr.execute(sql, vals)
	db_conn.commit()

def set_comment_active(db_id, active, timestamp):
	#not_active = not active
	#sql = f"update yt_comments SET active='{str(active)}' where id={db_id}"
	try:
		db_update_row('yt_comments','id',db_id,['active'],[int(active)],timestamp)
	except Exception as e:
		print(f"set_comment_active failed on {db_id}")

	## to do this, we need our own ID!

def get_latest_comment_db_id(comment_id):
	sql = f"SELECT max(id) from yt_comments WHERE yt_id='{comment_id}' and active=1"
	try:
		id = int(db_get_single_element(sql))
	except:
		print("[get_latest_comment_db_id failed]")
		id = 0
	return id

# can take either our database_id or the youtube id. YT id requires more qualification
def get_yt_comment_updatedAt(id):
	if (isinstance(id,int)):
		sql = f"SELECT yt_snippet_updatedAt FROM yt_comments WHERE id={id}"
	else:
		sql = f"SELECT yt_snippet_updatedAt FROM yt_comments WHERE yt_id='{id}' and active=1"
	#print(sql)
	date_string = db_get_single_element(sql)
	if (isinstance(date_string,str)):
		return date_string
	else:
		return ""

def db_insert_row(table, cols, vals, timestamp=True):
	if (timestamp):
		print("db_insert_row still has wrong timestamp method")
		cols.append('last_update')
		vals.append(datetime.datetime.now())
	(col_list,parameter_list) = build_insert_list(cols)
	#print(f"col_list: {col_list}")
	#print(f"parameter_list: {parameter_list}")
	try:
		curr = db_conn.cursor()
		curr.execute(f"INSERT INTO {table} ({col_list}) VALUES ({parameter_list})", vals)
		db_conn.commit()
		return True
	except Exception as e:
		print(f"[db_insert_row]: Insert failed:\n{e}\n\n")
		return False

def set_last_comment_check(date):
	curr = db_conn.cursor()
	sql = f"UPDATE meta SET last_comment_check='{date}'"
	try:
		curr.execute(sql)
		db_conn.commit()
		print("last_comment_check updated")
	except Exception as e:
		print(f"Update last_comment_check failed\n {e}")


def set_last_db_update(date):
	curr = db_conn.cursor()
	sql = f"UPDATE meta SET last_db_update='{date}'"
	try:
		curr.execute(sql)
		db_conn.commit()
		print("last_db_date updated")
	except Exception as e:
		print(f"Update last_db_date failed\n {e}")

##########################################
def main():
	print(f"Did you mean to run {path.basename(__file__)} standalone?")
	print(f"db_file: {db_file}")
	if (create_connection(db_file)):
		# no reason to do anything else, amirite?
		get_database_schema_version()
		last_db_update = get_last_db_update()
		
		#set_last_db_update("2023-09-21 09:12:04")

		# might as well.
		try:
			db_conn.close()
		except:
			print("Couldn't close db, maybe it wasn't open?")

	exit()


if __name__ == '__main__':
	main()
