import dbFace as df
import os # to check folder existance and create a new one
import shutil # to delete db folder recursively 
import sharedFuncs as sf # to get quoted vals for db query
import sharedVars as sv # for db name prefix
# import ctime # to create db_name and folder_name
# import sharedClasses as sc # to set data_types values in fb_col_descr
# attr_col_data_types_set = sc.AttrColDescr.data_types - связность модулей!!

def drop_db(db_name):
  query = 'DROP DATABASE IF EXISTS `' + db_name + '`'
  db_rows = df.connect_query_close(db_name, query)
  if type(db_rows).__name__ == 'str':
    return ['got error while trying to drop db:' + db_rows]
  return []
  
          
def mk_db_name(db_id):
  return sv.db_name_prefix + str(db_id)

def create_fuseblan_db(db_name, db_descr, db_obj = None):
  query_list = ['CREATE DATABASE IF NOT EXISTS `' + db_name + \
          '` CHARACTER SET utf8 COLLATE utf8_unicode_ci']
  query_list += ['USE `' + db_name + '`'] # use created db to make tables
  table_enum = sf.quoted_vals(sv.main_tables)
  query_list += ['CREATE TABLE IF NOT EXISTS `attributes`' + \
                '(col_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ' + \
                'table_name ENUM(' + table_enum + ') NOT NULL, ' + \
                'col_name VARCHAR(20) NOT NULL UNIQUE,' + \
                'col_group VARCHAR(60), ' + \
                'label VARCHAR(200), ' + \
                'data_type VARCHAR(30) NOT NULL, '
                'PRIMARY KEY(col_id))'] # attributes table
  query_list += ['CREATE TABLE IF NOT EXISTS `organisms`' + \
                '(org_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ' + \
                'org_name VARCHAR(100) NOT NULL, ' + \
                'PRIMARY KEY(org_id))'] # organisms table
  query_list += ['CREATE TABLE IF NOT EXISTS `enzymes`' + \
                '(org_id MEDIUMINT UNSIGNED NOT NULL, ' + \
                'enz_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ' + \
                'enz_name VARCHAR(60) NOT NULL, ' + \
                'PRIMARY KEY(enz_id), FOREIGN KEY (org_id) ' + \
                'REFERENCES organisms(org_id) ' + \
                'ON UPDATE CASCADE ON DELETE CASCADE)'] # enzymes table
  query_list += ['CREATE TABLE IF NOT EXISTS `subunits`' + \
                '(enz_id MEDIUMINT UNSIGNED NOT NULL, ' + \
                'su_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ' + \
                'su_name VARCHAR(60) NOT NULL, ' + \
                'su_seq TEXT NOT NULL, ' + \
                'PRIMARY KEY(su_id), FOREIGN KEY (enz_id) ' + \
                'REFERENCES enzymes(enz_id) ' + \
                'ON UPDATE CASCADE ON DELETE CASCADE)'] # subunits table
  query_list += ['CREATE TABLE IF NOT EXISTS `al_info`' + \
                '(al_id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ' + \
                'ctime FLOAT UNSIGNED NOT NULL, ' + \
                'enz_id_set TEXT NOT NULL, su_names TEXT NOT NULL, ' + \
                'filter_set TEXT, al_descr TEXT, ' + \
                'PRIMARY KEY(al_id))'] # al_info table
  query_list += ['CREATE TABLE IF NOT EXISTS `al_su_data`' + \
                '(al_id MEDIUMINT UNSIGNED NOT NULL, ' + \
                'su_name VARCHAR(60) NOT NULL, ' + \
                'al_length MEDIUMINT UNSIGNED NOT NULL, ' + \
                'block_markup TEXT, ' + \
                'PRIMARY KEY(al_id, su_name), '+ \
                'FOREIGN KEY (al_id) REFERENCES al_info(al_id) ' + \
                'ON UPDATE CASCADE ON DELETE CASCADE)'] # al_su_data table
  query_list += ['CREATE TABLE IF NOT EXISTS `al_data`' + \
                '(al_id MEDIUMINT UNSIGNED NOT NULL, ' + \
                'su_name VARCHAR(60) NOT NULL, ' + \
                'enz_id MEDIUMINT UNSIGNED NOT NULL, ' + \
                'al_seq TEXT NOT NULL, ' + \
                'PRIMARY KEY(al_id, su_name, enz_id), ' + \
                'FOREIGN KEY (al_id) REFERENCES al_info(al_id) ' + \
                'ON UPDATE CASCADE ON DELETE CASCADE, ' + \
                'FOREIGN KEY (al_id, su_name) ' + \
                'REFERENCES al_su_data(al_id, su_name) ' + \
                'ON UPDATE CASCADE ON DELETE CASCADE)'] # al_data table
  
  # print('<br>'.join(query_list))
  # try to create database:
  db_link, db_cursor = df.get_link_and_cursor()
  if type(db_link).__name__ == 'str' or type(db_cursor).__name__ == 'str':
    return ['Error creating database'] + [db_link] + [db_cursor]
  for query in query_list:
    result = df.send_query(db_cursor, query)
    if type(result).__name__ == 'str': #some error, delete db and say about it:
      # err_msg += ['Deleting new database due to SQL query error:' + str(result)]
      # del_result = delete_db(db_cursor, db_id)
      # if del_result:
        # err_msg += ['Got database deletion error:'] + del_result
      db_link.close()
      return [result]
  # if writing to db is ok - there could be folder error, now isn't critical
  status = ['New database "' + db_descr + '" has been created with name "' + \
            db_name + '"']
  if db_obj:
    if type(db_obj).__name__ != 'DbObj':
      status += ['Database object obtained from xml is incorrect']
    else:
      status += fill_db_from_db_obj(db_cursor, db_obj)
  db_link.commit()
  db_link.close()
  return status # + ['List of errors occured during creation:' ] + err_msg
 
#________________________insert section:___________________________

def insert_org(db_cursor, attr_col_names, org):
  col_names = ', '.join(['org_name'] + attr_col_names)
  vals = sf.mk_db_field_vals([org.name] + org.get_str_vals(attr_col_names))
  query = 'INSERT INTO `organisms` (' + col_names + ') VALUES (' + \
           vals + ')'
  return df.insert_query(db_cursor, query)
  
def insert_enz(db_cursor, attr_col_names, enz, org_id):
  col_names = ', '.join(['enz_name', 'org_id'] + attr_col_names)
  vals = sf.mk_db_field_vals([enz.name, str(org_id)] + \
                     enz.get_str_vals(attr_col_names))
  query = 'INSERT INTO `enzymes` (' + col_names + ') VALUES (' + \
           vals + ')'
  return df.insert_query(db_cursor, query)
  
def insert_su(db_cursor, attr_col_names, su, enz_id):
  col_names = ', '.join(['su_name', 'enz_id', 'su_seq'] + attr_col_names)
  vals = sf.mk_db_field_vals([su.name, enz_id, su.su_seq] + \
                      su.get_str_vals(attr_col_names))
  query = 'INSERT INTO `subunits` (' + col_names + ') VALUES (' + vals + ')'
  return df.insert_query(db_cursor, query)
  
def insert(db_cursor, table_name, col_names, vals):
  col_names = ', '.join(col_names)
  vals = sf.mk_db_field_vals(vals)
  query = 'INSERT INTO `' + table_name + '` (' + col_names + ') VALUES (' + \
           vals + ')'
  # print('insert query:', query, '<br>')
  return df.insert_query(db_cursor, query)
  
# def insert_al_info(db_cursor, ctime_int, enz_id_set, filter_set, su_names):
  # col_names = ['ctime', 'enz_id_set', 'filter_set', 'su_names']
  # vals = sf.mk_db_field_vals([ctime_int, enz_id_set, filter_set, su_names])
  # return insert(db_cursor, 'al_info', col_names, vals)
  
# def insert_al_seq(db_cursor, al_id, su_name, enz_id, al_seq):
  # col_names = ['al_id', 'su_name', 'enz_id', 'al_seq']
  # vals = sf.mk_db_field_vals([al_id, su_name, enz_id, al_seq])
  # return insert(db_cursor, 'al_data', col_names, vals)
  
# def insert_al_su_data(db_cursor, al_id, su_name, al_length, block_markup):
  # col_names = ['al_id', 'su_name', 'al_length', 'block_markup']
  # vals = [al_id, su_name, al_length, block_markup]
  # return insert_al(db_cursor, 'al_su_data', col_names, vals)
  
def fill_db_from_db_obj(db_cursor, db_obj):
  # get attribute col names for each of the main tables to make an 'INSERT': 
  o_attr_col_names = db_obj.attr_col_descr_list.get_table_col_names('organisms')
  e_attr_col_names = db_obj.attr_col_descr_list.get_table_col_names('enzymes')
  s_attr_col_names = db_obj.attr_col_descr_list.get_table_col_names('subunits')
  # alternate main tables structure with attribute cols described in DbObj
  # and insert these cols into 'attributes' table:
  status = add_attr_cols(db_cursor, db_obj.attr_col_descr_list)
  if status:
    return ['Altering table structure error:'] + status
  # fill in main tables:
  for org in db_obj.get_org_list():
    # insert organism info to 'organisms' table
    org_id = insert_org(db_cursor, o_attr_col_names, org)
    if type(org_id).__name__ == 'str': # what returns in case of in sertion error?
      status += ['Organism ' + org.name + ' db insertion error: ' + org_id]
      continue
    for enz in org.enz_list:
      # insert enzyme bound with organisms by org_id into 'enzymes' table 
      enz_id = insert_enz(db_cursor, e_attr_col_names, enz, org_id)
      if type(enz_id).__name__ == 'str':
        status += ['Enzyme ' + enz.name + ' db insertion error: ' + enz_id]
        continue
      for su in enz.su_list:
        su_id = insert_su(db_cursor, s_attr_col_names, su, enz_id)
        if type(su_id).__name__ == 'str':
          status += ['Subunit ' + su.name + ' db insertion error: ' + su_id]
  return status if status else []
  
def drop_attr_col(db_cursor, table_name, col_name):
  query = "DELETE FROM `attributes` WHERE table_name = '" + table_name + \
          "' AND col_name = '" + col_name + "'"
  print('drop query in de:', query, '<br>')
  result = df.send_query(db_cursor, query) 
  if type(result).__name__ == 'str':
    return result # don't drop columns if some fault in attributes occures
  query = 'ALTER TABLE `' + table_name + '` DROP ' + col_name
  return df.send_query(db_cursor, query)
  
def drop_attr_cols(db_cursor, attr_cols):
  err_msg = []
  if not attr_cols:
    return 'no column names were passed to drop them'
  for attr_col in attr_cols:
    col_name = attr_col.attr_col_descr.col_name
    table_name = attr_col.attr_col_descr.table_name
    err_msg.append(drop_attr_col(db_cursor, table_name, col_name))
  return err_msg   
  
def add_attr_col_descr(db_cursor, attr_col_descr): 
  attr_vals = sf.quoted_vals(attr_col_descr.all_vars_vals)
  query = 'INSERT INTO `attributes`(' + ', '.join(attr_col_descr.vars) + \
               ')  VALUES (' + attr_vals + ')'    
  return df.send_query(db_cursor, query) #ERR can be here
  
def add_attr_col_to_table(db_cursor, table_name, col_name):
  query = 'ALTER TABLE `' + table_name + '` ADD ' + col_name + ' TEXT'
  return df.send_query(db_cursor, query)  

def add_attr_col(db_cursor, attr_col):
  #add col descr to 'attributes', add col to table_name and write down col data
  acd = attr_col.attr_col_descr
  err_msg = add_attr_col_descr(db_cursor, acd)
  if type(err_msg).__name__ == 'str':
    return [err_msg]
  err_msg = add_attr_col_to_table(db_cursor, acd.table_name, acd.col_name)
  if type(err_msg).__name__ == 'str':
    return [err_msg]
  return write_attr_col_to_db(db_cursor, attr_col)
  
def add_attr_cols(db_cursor, attr_col_descr_list):
  err_msg = []
  #TODO: set col types according to data types! now just 'text' type
  for table in sv.main_tables:
    alter_query = 'ALTER TABLE `' + table + '` '
    for attr_col_descr in attr_col_descr_list.get_table_col_list(table):
      # insert attribute col info into 'attributes':
      result = add_attr_col_descr(db_cursor, attr_col_descr)
      if type(result).__name__ == 'str':
        err_msg.append(result)
        continue
      # if attribute description is written, add attribute col to 'ALTER' query:
      alter_query += ' ADD ' + attr_col_descr.col_name + ' ' + \
                     attr_col_descr.get_db_col_type() + ','
    query = alter_query[:-1] # fix 'ALTER' query: erase last ','
    # alternate current table with new attribute columns:
    result = df.send_query(db_cursor, query)
    if type(result).__name__ == 'str':
      err_msg.append(result)
  return err_msg

def write_attr_col_to_db(db_cursor, attr_col, upd_descr = False):
  # writes vals from attr col to table_name.col_name where id = value id
  acd, err_msg = attr_col.attr_col_descr, []
  id_name = sf.get_id_name(acd.table_name)
  #if upd_descr, change attr col description in `attributes`:
  if upd_descr and acd.var_to_val: # values are not empty
    query = "UPDATE `attributes` SET "
    for var, val in acd.var_to_val.items():
      query += var + " = '" + str(val) + "', "
    # kill the last comma came from "for" cycle and send "update" query
    query = query[:-2] + " WHERE table_name = '" + acd.table_name + \
            "' AND col_name = '" + acd.col_name + "'"
    # print('write attr col upd attr query:', query, '<br>')
    result = df.send_query(db_cursor, query)
    if result:
      err_msg.append(result)
  for id, val in attr_col.id_to_val.items():
    db_field_val = "'" + str(val) + "'" if val else 'NULL'
    query = "UPDATE `" + acd.table_name + "` SET " + acd.col_name + " = " + \
            db_field_val + " WHERE " + id_name + " = " + str(id)
    result = df.send_query(db_cursor, query)
    if type(result).__name__ == 'str':
      err_msg.append(result)
  return err_msg

    
