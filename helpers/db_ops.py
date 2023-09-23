import sqlite3
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
	
def db_get_single_element(sql): 
	curr = db_conn.cursor()
	curr.execute(sql)

	rows = curr.fetchall()
	if (len(rows) > 0): 
		if (isinstance(rows[0][0],int)):
			return f"{rows[0][0]}"
		else:
			return rows[0][0].strip()
	else:
		return None

def get_database_schema_version():
	version = db_get_single_element("SELECT database_version FROM meta")
	print(f"Database schema ver: {version}")
	return version

def get_last_db_update():
	last_db_update = db_get_single_element("SELECT last_db_update FROM meta")
	print(f"Last data dump: {last_db_update}")
	return last_db_update

def build_col_list(cols):
	col_list = ""
	parameter_list = ""
	for col in cols:
		col_list = col_list + "," + col
		parameter_list = parameter_list + ",?"
	col_list = col_list[1:]
	parameter_list = parameter_list[1:]
	#print(f"columns: {col_list}")
	return (col_list, parameter_list)

# insert is failing because tags are an array! 
# gah

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

def db_insert_row(table, cols, vals):
	(col_list,parameter_list) = build_col_list(cols)
	#print(f"col_list: {col_list}")
	#print(f"parameter_list: {parameter_list}")
	curr = db_conn.cursor()
	curr.execute(f"INSERT INTO {table}({col_list}) VALUES ({parameter_list})", vals)
	db_conn.commit()

def set_last_db_update(date):
	curr = db_conn.cursor()
	sql = f"UPDATE meta SET last_db_update='{date}'"
	try:
		curr.execute(sql)
		db_conn.commit()
		print("last_db_date upated")
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
