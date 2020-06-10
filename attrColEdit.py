#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

from contextlib import closing
import os # to see is there a databases.tx
from copy import deepcopy #to fill db_info_list
import cgi 
import cgitb
import dbFace as df
import xmler #to get attr from and put to file
import dbFace as df #to get some fields from db
import dbEdit as de #to update attr cols
import sharedClasses as sc # for AttrCol and other objects creation
import sharedFuncs as sf # to get id_to_names
import attrColEditHtml as ah
import sharedHtml as sh #to make page description
# import re #to parse attribute textarea field

 
def mk_acts_to_attr_cols(post_data, table_name):
  act_to_cols = {'edit': [], 'from_field' : [], 'to_file' : [], 
                 'delete' : []}
                 
  id_list = ah.get_id_list(post_data, table_name)
  # print('id_list:', id_list, '<br>')
  for col_name in ah.get_col_names(post_data):
    act = ah.get_action(post_data, col_name)
    if act == 'none':
      continue
    ac = ah.mk_attr_col_from_post(post_data, table_name, col_name)
    # print('attr col in mk_acts_to_attr_cols: type = ', ac.attr_col_descr.data_type, '<br>')
    if act == 'edit': # no readonly or disabled in this case, so it works
      #make attribute column and fill it in with values bound to ids
      ah.fill_attr_col_from_post(post_data, col_name, ac, id_list)
      # for id in id_list:
        # val = ah.get_attr_id_val(post_data, col_name, id)
        # ac.add_id_val(id, val)
    if act == 'from_field': 
    # doesn't eat attr col descr from post - even if inputs aren't "disabled"
    # but "readonly"! FFFuuu...
      # make attribute column from text in textarea field:
      ah.fill_attr_col_from_content_field(post_data, col_name, ac)
    act_to_cols[act].append(ac) #ERR: deepcopy?
  return act_to_cols
  
def mk_attr_descrs_from_db(db_cursor, table_name):
  acd_list = sc.AttrColDescrList()
  where_case = "WHERE table_name = '" + table_name + "'"
  attr_rows = df.get_attr_rows(db_cursor, where_case)
  if type(attr_rows).__name__ == 'str':
    return None, ['No attributes was obtained from ' + db_name + ' for ' + \
            table_name + ' ' + attr_rows]
  acd_list.fill_from_attr_rows(attr_rows)
  return acd_list, []
  
def mk_attr_cols_from_db(db_cursor, attr_col_descr_list):
  attr_cols = []
  for acd in attr_col_descr_list.all_cols:
    ac = sc.AttrCol(acd)
    query_cols = ', '.join([sf.get_id_name(table_name), acd.col_name])
    query = 'SELECT ' + query_cols + ' FROM `' + table_name + '`'
    attr_val_rows = df.send_query(db_cursor, query)
    ac.fill_from_db_rows(attr_val_rows)
    attr_cols.append(deepcopy(ac))
  return attr_cols
  
def get_max_col_id(db_cursor, table_name):
  prefix = sf.get_col_name_prefix(table_name) + '_'
  query = 'SELECT col_name FROM `attributes` WHERE col_name LIKE "' + \
          prefix + '%"'
  result = df.send_query(db_cursor, query)
  if type(result).__name__ == 'str':
    return ['cannot get the latest column id:' + result]
  id_str = []
  for row in result: #get full col name, cut off prefix then get id
    col_id = sf.try_val_to_int(row.get('col_name', '')[len(prefix):])
    if col_id:
      id_str.append(col_id)
  return max(id_str) if id_str else 0
  # if max_col_id == -1:
    # return ['database query result for the latest column id does not ' + \
                      # 'contain "MAX(col_id)" key']
  # return max_col_id  
          
def load_data_from_db(db_cursor, table_name):
  acd_list, status = mk_attr_descrs_from_db(db_cursor, table_name)
  if not acd_list:
    return '', status
  max_id = get_max_col_id(db_cursor, table_name)
  groups = acd_list.get_groups()
  attr_cols = mk_attr_cols_from_db(db_cursor, acd_list)
  id_to_name = sf.get_id_to_name(db_cursor, table_name)
  df.close_db(db_link)
  id_list = sorted(id_to_name.keys())
  col_names = acd_list.get_table_col_names(table_name)
  groups = acd_list.get_groups()
  html = ah.mk_metadata(db_name, table_name, col_names, groups, id_list, max_id)
  html += ah.mk_panel(table_name, attr_cols, id_list, id_to_name).get_html()
  html += ah.mk_footer(table_name, id_to_name)
  return html, [] 
  
# def update_attrs_from_fields(db_cursor, post_data, attr_cols):
  # if not attr_cols:
    # return []
  # # col_name_to_attr_col = dict()
  # for attr_col in attr_cols:
    
  # return update_attrs_from_attr_cols(db_cursor, attr_cols)
  
def update_attrs_from_attr_cols(db_cursor, attr_cols, upd_descr = False):
  #if action is 'edit' - there's attr col descr available, upd_descr = True
  if not attr_cols:
    return []
  status = []
  for attr_col in attr_cols:
    status += de.write_attr_col_to_db(db_cursor, attr_col, upd_descr)
  return status

def delete_attrs(db_cursor, attr_cols):
  if not attr_cols:
    return []
  col_labels = []
  for col in attr_cols:
    col_labels.append(col.attr_col_descr.label)
  result = de.drop_attr_cols(db_cursor, attr_cols)
  if type(result).__name__ == 'str':
    return ['attribute(s) deletion error:', result]
  return ['attribute(s) ' + ', '.join(col_labels) + ' is (are) deleted']
  
# def get_attrs_to_file(db_cursor, table_name, attr_cols, dest_xml):
  # return []
  
  
def mk_attr_col_descr_list(table_name, post_data):
  acd_list = sc.AttrColDescrList()
  max_id = int(ah.get_last_col_id(post_data))
  col_num = int(ah.get_add_col_num(post_data))
  for i in range(1, col_num+1):
    col_name = ah.mk_attr_col_name(table_name, max_id + i)
    acd = ah.mk_attr_col_descr_from_post(post_data, table_name, col_name)
    acd_list.add_col(acd)
  return acd_list
  
def add_attributes(db_cursor, table_name, post_data):
  acd_list = mk_attr_col_descr_list(table_name, post_data)
  return de.add_attr_cols(db_cursor, acd_list)
  
def do_actions(db_cursor, table_name, post_data):
  #act_to_cols is a dict of dicts: {act:{col_name:attr_col}}
  status, acd_list = [], None
  if sh.get_action(post_data) == 'add': #called from addCol.py
    status += add_attributes(db_cursor, table_name, post_data)
  act_to_cols = mk_acts_to_attr_cols(post_data, table_name)
  status += delete_attrs(db_cursor, act_to_cols['delete'])
  #if action is 'edit' - there's attr col descr available, upd_descr = True
  status += update_attrs_from_attr_cols(db_cursor, act_to_cols['edit'], True)
  #if action is 'from_field' - forget about reading description from post >((
  status += update_attrs_from_attr_cols(db_cursor, act_to_cols['from_field'])
  # status += get_attrs_to_file(db_cursor, table_name, 
                              # act_to_cols['to_file'])
  # status += update_attrs_from_file(db_cursor, table_name, 
                              # act_to_cols['from_file'])
  
  return status
    
cgitb.enable()  
post_data = cgi.FieldStorage()

page_name, page_label, status, content, html = 'attrColEdit.py', '', [], '', ''
if not post_data:
  html = sh.mk_page_header(page_name, status, page_label, no_post_data = True)
else:
  db_name = sh.get_db_name(post_data)
  table_name = ah.get_table_name(post_data)
  db_link, db_cursor = df.get_link_and_cursor(db_name)
  if not db_cursor:
    status = ['Cannot connect to database ' + db_name]
  else:
    page_label = ' of ' + table_name + ' in database ' + db_name
    status = do_actions(db_cursor, table_name, post_data)
    content, load_status = load_data_from_db(db_cursor, table_name)
    if not content:
      status += load_status
  df.close_db(db_link)
  html = sh.mk_page_header(page_name, status, page_label) + content

print(html)
 
