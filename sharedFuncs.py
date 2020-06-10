import re
import sharedHtml as sh
import dbFace as df
import sharedClasses as sc

def check_dict_keys(keys, dict_to_check):
  if type(dict_to_check).__name__ != 'dict' or type(keys).__name__ != 'list':
    return False
  if to_set(keys) <= to_set(dict_to_check.keys()):
    return True
  return False
  
def to_set(vals):
  if type(vals).__name__ == 'str':
    return set([vals])
  return set(vals)

def get_col_name_prefix(table_name):
  if table_name in ['organisms', 'enzymes']:
    return table_name[:3]
  if table_name in ['subunits', 'alignments']:
    return table_name[:2]
  return ''

def get_id_name(table_name):
  prefix = get_col_name_prefix(table_name)
  return prefix + '_id' if prefix else ''
  
def get_name_col_name(table_name):
  prefix = get_col_name_prefix(table_name)
  return prefix + '_name' if prefix else ''
  
def replace_ill_symbols(data): # avoid of illicit symbols
  ill_symbols = {'"': '&#34;', "'":'&#39;', ";":'&#59;', '&':'&#38;', 
                 '*':'&#42;', '`':'&#96;'}
  valid = ''
  for l in str(data):
    valid += ill_symbols.get(l, l)
  return valid
  
def quoted_vals(val_list):
  if type(val_list).__name__ in ['list', 'set']:
    val_list = [replace_ill_symbols(val) for val in val_list]
    return "'" + "', '".join(val_list) + "'"
  return ""
  
def quoted_str_to_db_field(quoted_str):
  #all quotes in str are replaced by \' in result str. For string  
  #representations of python objects (set(), list(),..)  to write them to db
  return re.sub("'","\\'" , quoted_str)
  
def mk_db_field_vals(val_list):
  #to alter or insert record values must be NULL (not quoted) for int and float
  #columns, so '' must be replaced with NULL
  df_vals = ''
  # print('val_list:',val_list, '<br>')
  if type(val_list).__name__ in ['list', 'set']:
    for val in val_list:
      # print('val:', val, '<br>')
      if type(val).__name__ in ['list', 'set', 'dict']:
        # print('got list val<br>')
        val = quoted_str_to_db_field(str(val))
        # val = replace_ill_symbols(val)
      else: #if val is a list of strings its str() representation has quotes
        #so str(val) turns to bytes
        # print('got str val<br>')
        val = replace_ill_symbols(str(val))
      # print('now val is:', val, '<br>')
      df_vals += '"' + val + '", ' if val else 'NULL, '
      # df_vals += '"' + str(val) + '", "' if val else 'NULL, '
    # print('df_vals:', df_vals, '<br>')
  return df_vals[:-2] if len(df_vals) > 2 else df_vals
  
def get_where_id_case(id_set, table_name, join_tables = False):
  id_set_str = ''
  if id_set:
    if type(id_set).__name__ == 'set':
      id_set_str = str(id_set).replace('{','(').replace('}',')')
    if type(id_set).__name__ == 'list':
      id_set_str = str(id_set).replace('[','(').replace(']',')')
    id_name = get_id_name(table_name)
    if join_tables: # if there's a JOIN in SELECT query, id column has name 
                    # e.enz_id or o.org_id instead enz_id or org_id
      id_name = table_name[0] + '.' + id_name
    where_case = id_name + ' IN ' + id_set_str
    return where_case
  return ''
  
def get_enz_id_to_enz_descr(db_cursor, enz_id_set = set()):
  enz_id_to_names = dict()
  where_case = get_where_id_case(enz_id_set, 'enzymes', True)
  query = "SELECT o.org_id, o.org_name, e.enz_id, e.enz_name FROM " + \
          "organisms o INNER JOIN enzymes e ON e.org_id = o.org_id "
  query += ' WHERE ' + where_case if where_case else ''
  db_rows = df.send_query(db_cursor, query)
  if type(db_rows) != 'str':
    for row in db_rows:
      enz_descr = sc.EnzDescr(row.get('enz_id', 0), row.get('enz_name', ''),
                              row.get('org_id', 0), row.get('org_name', ''))
      enz_id_to_names[enz_descr.enz_id] = enz_descr
  return enz_id_to_names
  
def get_id_to_name(db_cursor, table_name):
  #TODO*: usage for every main table! (now - only for 'organisms') - ready?
  query, id_to_name, id_name = 'SELECT', dict(), get_id_name(table_name)
  if table_name == 'organisms':
    query += ' org_id, org_name FROM `organisms`'
  if table_name == 'enzymes':
    query += ' enz_id, org_name, enz_name FROM `organisms` o INNER JOIN ' + \
             '`enzymes` e on o.org_id = e.org_id ORDER BY o.org_name'
  if table_name == 'subunits':
    query += ' su_id, org_name, enz_name, su_name FROM `organisms` o ' + \
             'INNER JOIN `enzymes` e on o.org_id = e.org_id INNER JOIN ' + \
             '`subunits` s on e.enz_id = s.enz_id ORDER BY o.org_name'
  db_rows = df.send_query(db_cursor, query) 
  for row in db_rows:
    if id_name not in row.keys():
      continue
    name = row['org_name']
    if 'enz_name' in row.keys():
      name += '##' + row['enz_name']
    if 'su_name' in row.keys():
      name += '##' + row['su_name']
    id_to_name[row[id_name]] = name
  return id_to_name
  
def mk_regexp_of_loose_name(loose_name):
  l_n_parts = re.split(r'\W', loose_name) # break loose_name on words
  regexp_parts = []
  for part in l_n_parts:
    if part.isalpha(): #leave only words consist of letters
      regexp_parts.append(part)
  return "(?:" + '|'.join(regexp_parts) + ")"
  
def get_loose_name_to_id(id_to_name, loose_names_list):
  l_n_to_id, l_n_to_rexp = dict(), dict()
  for l_n in loose_names_list:
    l_n_to_rexp[l_n] = mk_regexp_of_loose_name(l_n)
  for l_n, rexp in l_n_to_rexp.items():
    for id, name in id_to_name.items():
      if re.findall(rexp, name, flags = re.IGNORECASE):
        l_n_to_id[l_n] = id
  return l_n_to_id

def add_to_key_to_list(key_to_list, key, val):
    if key not in key_to_list.keys():
      key_to_list[key] = []
    key_to_list[key].append(val)
    
def get_num_val_from_str(str_val):
  if str_val:
    try:
      return int(str_val)
    except ValueError:
      try:
        return round(float(str_val), 2)
      except ValueError:
        return None
        
def to_str(val):
  # print('val:', val, 'val_type: ', type(val).__name__, '<br>')
  return str(val) if val else ''
  
def float_to_str(val, prec):
  return str(round(val,prec))
  
def try_val_to_int(any_val):
  if type(any_val).__name__ != 'int':
    if str(any_val).isnumeric():
      return int(any_val)
    return None
  return any_val
  
def try_val_to_float(any_val):
  r_exclude, r_exact = '[^0-9.]', '^\d+.\d+'
  if type(any_val).__name__ != 'float':
    any_val_str = str(any_val)
    #if any_val has any other symbol than digit or dot 
    if re.findall(r_exclude, any_val_str): 
      return None
    if re.findall(r_exact, any_val_str):
      return float(any_val_str)
    return None
  return any_val
        
def bin_file_to_lines(bin_file):
  #returns file lines if file was sent as binary through post_data, \r discarded
  if not bin_file or type(bin_file).__name__ != 'bytes':
    return []
  lines = bin_file.decode('utf-8').replace('\r', '').split('\n')
  return lines
  
# def replace_query_ill_symbols(line):
  # ill_symbols = {'"': '&#34;', "'":'&#39;', ";":'&#59;', '&':'&#38;', 
                 # '*':'&#42;', '`':'&#96;'}
  # valid = ''
  # for l in str(data):
    # valid += ill_symbols.get(l, l)
  # return valid
  
# def get_page_parents(page_name):
  

    
      
      
      
    