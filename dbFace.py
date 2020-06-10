#a Fuseblan database interface: change for proper python-MySQL connector.
#All cursors have to be of a dict type, namely return data rows in format 
#[table_col_name] = 'cell_value'
#Also is using to get info from db
import MySQLdb
import sharedVars as sv # 'user' and 'passwd' configure
import xmler # to create db from xml and save db to xml
import sharedClasses as sc # to fill db from / get db to OrgList
import sharedFuncs as sf # get id column name by table name

def connect_db(db_name = None): #connect to a specific db - when its name is known
  try:
    if db_name:
      return MySQLdb.connect(user = sv.db_params['user'], 
                                passwd = sv.db_params['passwd'],
                                db = db_name)
    else:
      return MySQLdb.connect(user = sv.db_params['user'], 
                                passwd = sv.db_params['passwd'],
                                )
  except MySQLdb.Error as me:
    return str(me)
  except Exception as e:
    return str(e)
  return 'Unknown error while connecting to database ' + db_name

  
def get_dict_cursor(db_link):
  db_cursor = db_link.cursor(MySQLdb.cursors.DictCursor)
  return db_cursor
  
def get_link_and_cursor(db_name = None):
  db_link = connect_db(db_name) # should here be a db name, if it's being dropped?
  if is_link(db_link):
    db_cursor = get_dict_cursor(db_link)
    if is_cursor(db_cursor):
      return db_link, db_cursor
    close_db(db_link)
  return None, None
    
def check_db_exists(db_name):
#??? when db is locked with another db_link, returns False even if db is exist
  db_link = connect_db(db_name)
  if is_link(db_link):
    db_link.close()
    return True
  return False

def send_query(db_cursor, query):
  #TODO: а если пустой словарь вернулся не из-за нулевого fetchall при успехе,
  #а из-за пустого dict(), возвращённого после исключения? как различить?
  try:
    # query = check_data(query)
    db_cursor.execute(query)
    db_rows = db_cursor.fetchall()
    # print('db_rows:', db_rows)
    # for row in db_rows:
      # for key, val in row.items():
        # if type(val) == 'float':
          # row[key] = round(val, 2)
    # if type(db_rows).__name__ == 'tuple' and len(db_rows) == 1:
      # return db_rows[0]
    return db_rows #iterable tuple of dict
  except MySQLdb.Error as me:
    return str(me)
  except Exception as e:
    return str(e) 
  return dict() #empty dict is False
  
def insert_query(db_cursor, query):
  try:
    # query = check_data(query)
    # print('insert query:', query, '<br>')
    db_cursor.execute(query)
    return db_cursor.lastrowid
  except MySQLdb.Error as me:
    return str(me)
  except Exception as e:
    return str(e)
  return 0 
  
def close_db(db_link):
  try:
    db_link.commit()
    db_link.close()
  except Exception as e:
    pass
  
def is_link(db_link):
  return type(db_link).__name__ == 'Connection'
  
def is_cursor(db_cursor):
  return type(db_cursor).__name__ == 'DictCursor'

def check_data(data): # avoid of SQL injection ?
  return str(data)
  
def connect_query_close(db_name, query):
  #open connection, query it, commit and close
  db_link, db_cursor = get_link_and_cursor(db_name)
  if db_link and db_cursor:
    # query = check_data(query)
    db_rows = send_query(db_cursor, query)
    close_db(db_link)
    return db_rows
  return dict()
  
def get_db_rows(db_cursor, where_case = ''):
  query = "SELECT * FROM organisms o INNER JOIN enzymes e " + \
          "ON e.org_id = o.org_id INNER JOIN subunits s " + \
          "ON s.enz_id = e.enz_id " + where_case + " ORDER BY o.org_id"
  # print('db rows query: ', query, '<br>')
  return send_query(db_cursor, query)
  
def get_attr_rows(db_cursor, where_case = ''):
  query = "SELECT * FROM `attributes` " + where_case + " ORDER BY table_name"
  return send_query(db_cursor, query)
  
def get_attr_and_db_rows(db_name):
  db_link, db_cursor = get_link_and_cursor(db_name)
  if not db_cursor:
    close_db(db_link)
    return ['No db connection to get attributes', 'No db connection to get data']
  db_rows = get_db_rows(db_cursor)
  attr_rows = get_attr_rows(db_cursor)
  # if type(attr_rows).__name__  == 'str':
    # return ['Cannot get rows from attributes table ' + attr_rows]
  # if type(db_rows).__name__ == 'str':
    # return ['Cannot get rows from organisms + enzymes + subunits tables ' + \
            # db_rows]
  close_db(db_link)
  return [attr_rows, db_rows]
