#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

from contextlib import closing
import os # to see is there a databases.tx
from copy import deepcopy #to fill db_info_list
import cgi 
import cgitb
import sharedHtml as sh
import dbFace as df
from time import ctime # to create db_name and folder_name
import xmler
import sharedClasses as sc # to make DbObj for xmler to dump db in xml
import sharedFuncs as sf # to make org_list
import sharedVars as sv #for db_name prefix
import fsMan as fs #to create and delete folders
import re # to parse databases.txt
import dbHtml as dh #to show the page
import dbEdit as de #to create, update and drop db

#databases.txt file structure:
#fb_1||here is some db description
#!no other symbols but digits and fb_ are allowed before ||!

def mk_db_name(db_id):
  return sv.db_name_prefix + str(db_id)
  
def mk_db_id(db_name):
  if type(db_name).__name__ == 'str' and db_name.startswith(sv.db_name_prefix):
    return int(db_name[len(sv.db_name_prefix):])
  return 0
    
class DbInfo:
  def update_last_id(self, name):
    id = mk_db_id(name)
    if id > self.last_id:
      self.last_id = id # count last_id
  def __init__(self):
    self.name_to_descr = dict()
    self.last_id = 0
    with closing(open('databases.txt', 'r')) as db_file:
      for db_line in db_file:
        # print('dbinfo init got line from db_file:', db_line, '<br>')
        db_attrs = re.split('##', db_line)
        if len(db_attrs) == 2 and db_attrs[0].startswith(sv.db_name_prefix):
          name, descr = db_attrs[0], db_attrs[1]
          self.name_to_descr[name] = descr # put db info to dict
          self.update_last_id(name)
  def dump_to_file(self):
    with closing(open('databases.txt', 'w')) as db_file:
      names_list = sorted(self.name_to_descr.keys(), reverse = True)
      for name in names_list:
        db_line = name + '##' + self.name_to_descr[name] + '\n'
        # print('dfinfo dump to file got line:', db_line, '<br>')
        db_file.write(db_line)
  def delete_db_info(self, db_name):
    erased = self.name_to_descr.pop(db_name, None)
    return [] if erased else ['db with name '+ db_name + \
            ' is absent in databases description, can\'t delete it']
  def add_db_info(self, db_name, db_descr):
    if db_name in self.name_to_descr.keys():
      return ['db name ' + db_name + ' is always present in databases ' + \
              'description, can\'t add database']
    self.name_to_descr[db_name] = db_descr
    self.update_last_id(id)
  def update_db_info(self, db_name, db_descr):
    if db_name not in self.name_to_descr.keys():
      return ['db with name '+ db_name + \
            ' is absent in databases description, can\'t update it']
    self.name_to_descr[db_name] = db_descr
  
def create_db_from_xml(db_name, db_descr, xml_src_file):
  # db_obj = xmler.get_db_obj_from_xml(xml_src_file)
  try:
    db_obj = xmler.get_db_obj_from_xml(xml_src_file)
  except Exception as e:
    return ['Error during filling database from xml' + str(e)]
  # if xml is incorrect, db_obj is [] of err_str
  if type(db_obj).__name__ == 'list': 
    return ['Error during filling database from xml'] + db_obj
  status = de.create_fuseblan_db(db_name, db_descr, db_obj)
  return status #return filling in info
  
def add_db(db_descr, xml_source, db_info):
  #decide whether to create db and fill it in from xml or leave empty
  #if xml is incorrect or description is empty, no database is created.
  if not db_descr:
    return ['Can\'t add database with empty description']
  db_name = mk_db_name(db_info.last_id + 1) #sets cursor on `fb_metadata`
  status = fs.create_db_folder(db_name)
  if xml_source:# xml file is provided by user, check xml, if correct - create 
    #db and then fill it from xml
    status += create_db_from_xml(db_name, db_descr, xml_source)
  else: # xml file isn't provided, create empty db:
    status += de.create_fuseblan_db(db_name, db_descr)
   # if new db is available for connection - add it to db_info
  if df.check_db_exists(db_name): 
    db_info.add_db_info(db_name, db_descr)
  return status
  
def upd_descr(db_name_to_descr, db_info):
  for db_name, db_descr in db_name_to_descr.items():
    db_info.update_db_info(db_name, db_descr)
  
def mk_xml(db_name):
  if not db_name.startswith(sv.db_name_prefix):
    return ['Got wrong database name for xml dump: ' + db_name]
  db_obj = sc.DbObj()
  attr_rows, db_rows = df.get_attr_and_db_rows(db_name)
  db_obj.set_from_db_rows(db_rows, attr_rows)
  xml_file = fs.open_db_dump_file(db_name, 'w')
  xmler.mk_xml_from_db_obj(db_obj, xml_file)
  return ['database ' + db_name + ' is dumped']
  # else:
    # return ['cannot dump database ' + db_name]
    
    
def delete_db(db_name, db_info):
  del_err = de.drop_db(db_name) # drop db
  if del_err:
    return ['Cannot drop database ' + db_name + ':'] + del_err
  # if db is dropped - folder can be deleted
  del_err_start = 'Database ' + db_name + ' is dropped'
  del_err = db_info.delete_db_info(db_name) # discard db info
  del_err += fs.delete_db_folder(db_name) # delete db folder
  if del_err:
    return [del_err_start + ' but some errors occured:'] + del_err
  return [del_err_start + ' folder ' + db_name + ' is deleted, ' + \
          ' data cleaned up']

def do_action(post_data, db_info):
  status = []
  # db_name = dh.get_chosen_db_name(post_data)
  db_name = sh.get_db_name(post_data)
  action = sh.get_action(post_data)
  # gather db descriptions checked for update and update them
  db_name_to_descr_update = dh.get_descr_to_update(post_data)
  # get the kind of action described in dbHtml:
  if db_name and action == dh.del_act:
    #drop db then delete db folder and discard db record from db_info
    print('db name to delete:', db_name, '<br>')
    status = delete_db(db_name, db_info) 
  if db_name and action == dh.get_xml_act: 
    status = mk_xml(db_name) # make xml and send it to user
  if action == dh.add_act: # get db description, create db and db folder and 
    # fill them from xml if given
    descr, xml_src_file = dh.get_add_data(post_data)
    status = add_db(descr, xml_src_file, db_info)
  if action == dh.upd_act:
    upd_descr(db_name_to_descr_update, db_info)
  db_info.dump_to_file() # ERR?
  return status

cgitb.enable()  
post_data = cgi.FieldStorage()
db_info, status = DbInfo(), []
if post_data:
  act_result = do_action(post_data, db_info)
  status += act_result

html = sh.mk_page_header('dbMan.py', status)
html += dh.mk_main_form(db_info)

print(html)
    
    
   
    
      