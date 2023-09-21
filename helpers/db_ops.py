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
