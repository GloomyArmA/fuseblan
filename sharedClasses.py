from copy import deepcopy
from abc import ABCMeta, abstractmethod
import sharedFuncs as sf #to add val list to one key in dict
import dbFace as df
import re

class EnzDescr:
  def __init__(self, enz_id, enz_name, org_id, org_name):
    enz_id, org_id = sf.try_val_to_int(enz_id), sf.try_val_to_int(org_id)
    self.enz_id = enz_id if enz_id else 0
    self.org_id = org_id if org_id else 0
    self.enz_name, self.org_name = enz_name, org_name
    self.name_str = enz_name + ' of ' + org_name
    self.id_name_str = str(enz_id) + ': ' + self.name_str
    
  def __str__(self):
    return self.name_str

class DataObj:
  #__metaclass__ = ABCMeta
  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.attr_to_val = dict()
    
  def fill_attr(self, attr_names, any_dict):
    if type(any_dict).__name__ == 'dict':
      for attr_name in attr_names:
        self.attr_to_val[attr_name] = any_dict.get(attr_name, None)
  
  def get_str_vals(self, attr_list):
    vals = [sf.to_str(self.attr_to_val.get(attr, None)) for attr in attr_list]
    return vals
    
class Organism(DataObj):
  @staticmethod
  def mk_gen_spec_name(org_name):
    if type(org_name).__name__ != 'str':
      return 'Wrong org_name'
    org_name = org_name.strip()
    if org_name.startswith('Candidatus') or org_name.startswith('candidatus'):
      org_name = org_name[(len('candidatus') -1):]
    on_parts = org_name.split()
    if on_parts and len(on_parts) >= 2:
      gen_spec = [on_parts[i].replace(' ', '') for i in [0, 1]]
      return ('_'.join(gen_spec))
    return 'Wrong org_name'
    
  def __init__(self, org_id, org_name):
    super().__init__(org_id, org_name)
    #self.gen_spec = Organism.mk_gen_spec_name(org_name)
    self.enz_list = []
    self.enz_id_to_enz = dict()
    
  def add_enzyme(self, enz):
    if type(enz).__name__ == 'Enzyme':
      self.enz_list.append(deepcopy(enz))
      if enz.id:
        self.enz_id_to_enz[enz.id] = self.enz_list[-1]
      
  def add_enzymes(self, enz_list):
    for enz in enz_list:
      self.add_enzyme(enz)
  
    
class Enzyme(DataObj):
  def __init__(self, enz_id, enz_name, org_id = 0):
    super().__init__(enz_id, enz_name)
    self.org_id = org_id
    self.su_list = []
    self.su_name_to_su_list = dict()
    self.su_names_union = set()
    self.su_id_to_su = dict()
    
  def add_subunit(self, su):
    if type(su).__name__ == 'Subunit':
      self.su_list.append(deepcopy(su))
      self.su_names_union.add(su.name)
      #because of not the only subunit with the same name su_names_to_su's
      #structure is [name] = [su_1, su_2, ...]
      sf.add_to_key_to_list(self.su_name_to_su_list, su.name, self.su_list[-1])
      if su.id:
        self.su_id_to_su[su.id] = self.su_list[-1]
      
  def add_subunits(self, su_list):
    for su in su_list:
      self.add_subunit(su)
    
  # def get_su_set(self):
    # return set(self.su_list)
    
  def get_su_seq(su_id):
    seqs = []
    for su in self.su_list:
      if su.name == su_name:
        seqs.append(su.su_seq)
    return seqs
        
    
class Subunit(DataObj):
  def __init__(self, su_id, su_name, su_seq, enz_id = 0):
    super().__init__(su_id, su_name)
    self.su_seq = su_seq
    self.enz_id = enz_id
    
class AttrColDescr:
  #data_types contains processable data types for attribute
  #ranks is a type similar with enum: it can be splitted on ranks. If col 
  #has values "F" "F" "N" "F" "F", it has two ranks: "F" and "N".
  #text is a usual text different from record to record so it can't be 
  #splitted on ranks
  #range is a text of '3.5 - 8' interpreting as two numbers: start 
  #(from 3.5) and end (to 8) of some range. There are two types of 
  #ranges - ceil_range, for ceil numbers, and float_range, for dotted as 3.5
  #nums are positive or negative (or zero) numbers, ceil (ceil_num) or
  #dotted as 3.5 (float_num)
  #id is a positive ceil number
  data_types = ['ranks', 'text', 'ceil_range', 'float_range', 'ceil_num', 
                'float_num', 'id']
  vars = ['table_name', 'col_name', 'label', 'data_type', 'col_group']
  def _set_vars_vals(self):
    # self.all_vars_vals = [eval('self.'+ p) for p in self.vars]
    for var in AttrColDescr.vars:
      val = eval('self.' + var)
      self.all_vars_vals.append(val) # needed by first units: dbMan, dbFace,..
      self.var_to_val[var] = val

  def __init__(self, table_name, col_name, label, data_type, col_group):
    self.table_name = table_name # name of db table containing attribute
    self.col_name = col_name # name in db table
    self.label = label # attribute description for user
    self.data_type = data_type if data_type in AttrColDescr.data_types else 'text'
    self._set_db_col_type()
    self.col_group = col_group # to make filtering and viewing convenient
    self.all_vars_vals = [] # all AttrColDescr object values ordered as vars
    self.var_to_val = dict()
    self._set_vars_vals()
    
  def get_var_to_val(self):
    return self.var_to_val
    
  def get_db_col_type(self):
    return self.db_col_type
    
  def _set_db_col_type(self):
    # if self.data_type in ['ranks', 'text', 'ceil_range', 'float_range']:
      # self.db_col_type = 'TEXT'
    if self.data_type == 'float_num':
      self.db_col_type = 'FLOAT'
    elif self.data_type == 'ceil_num':
      self.db_col_type = 'BIGINT'
    elif self.data_type == 'id':
      self.db_col_type = 'INT'
    else:
      self.db_col_type = 'TEXT'

class AttrCol:
  def __init__(self, attr_col_descr):
    self.attr_col_descr = deepcopy(attr_col_descr)
    self.id_to_val = dict() # dict {id : val}
    self.val_to_id_list = dict() # dict of {val2 = [id1, id3, ...]}
    
  def fix_val_type(self, val):
    float_rexp = '-*\d{1,}\.\d{1,}' #can be '-' and has to have ceil part 
    #(at least one digit) and fraction part (after one '.', at least one digit)
    ceil_rexp = '-*\d{1,}' #can be '-' and has to be at least one digit
    # db_ct = self.attr_col_descr.get_db_col_type()
    val_str = sf.to_str(val)
    dt = self.attr_col_descr.data_type
    if dt == 'id':
      return int(val_str) if val_str.isnumeric() else None
    if dt == 'ceil_num':
      ceil_num = re.findall(ceil_rexp, val_str)
      return int(ceil_num[0]) if ceil_num else None
    if dt == 'float_num':
      float_num = re.findall(float_rexp, val_str)
      return float(float_num[0]) if float_num else None
    if self.attr_col_descr.get_db_col_type() == 'TEXT':
      return val_str
    return val

  def add_id_val(self, id, val):
    val = self.fix_val_type(val)
    if type(id).__name__ == 'int':#and val:
      self.id_to_val[id] = val
      sf.add_to_key_to_list(self.val_to_id_list, val, id)
    
  def fill_from_db_rows(self, db_rows):
    # db_row is a "{'id_name':'id_val','col_name':'col_val'}"
    col_name = self.attr_col_descr.col_name
    id_name = sf.get_id_name(self.attr_col_descr.table_name)
    for row in db_rows:
      if sf.check_dict_keys([id_name, col_name], row):
        self.add_id_val(row[id_name], row[col_name])
    
  #TODO: def mk_filtered_attr_col(self, filter):
    # # returns AttrCol of id-vals passing filter
   
class AttrColDescrList:
  def __init__(self):
    self.all_cols = []
    self.group_to_cols = dict()
    self.table_name_to_cols = dict()
    self.col_name_to_cols = dict()
    
  def fill_from_attr_rows(self, attr_rows):
    #ERR: no attr_rows given
    for row in attr_rows:
      # print('got attr row:', row, '<br>')
      if sf.check_dict_keys(AttrColDescr.vars, row):
        #make AttrColDescr from db_row and add it to AttrColDescrList:
        self.add_col(AttrColDescr(row['table_name'], row['col_name'], 
                             row['label'], row['data_type'], row['col_group']))

  def add_col(self, attr_col_descr):
    if type(attr_col_descr).__name__ != 'AttrColDescr':
      print('AttrColDescrList.add_col() got wrong col type')
      return
    self.all_cols.append(attr_col_descr)
    sf.add_to_key_to_list(self.group_to_cols, attr_col_descr.col_group, 
                          attr_col_descr)
    sf.add_to_key_to_list(self.table_name_to_cols, attr_col_descr.table_name, 
                          attr_col_descr)
    self.col_name_to_cols[attr_col_descr.col_name] = attr_col_descr
    
  def get_table_col_list(self, table_name):
    return self.table_name_to_cols.get(table_name, [])
    
  def get_group_to_cols(self):
    return self.group_to_cols
    
  def get_groups(self):
    return sorted(self.group_to_cols.keys())
    
  def get_table_col_names(self, table_name):
    col_names = []
    for col in self.all_cols:
      if col.table_name == table_name:
        col_names.append(col.col_name)
    return col_names
    
  def get_group_col_list(self, group):
    return self.group_to_cols.get(group, [])
  
  def get_col_by_name(self, col_name):
    return self.col_name_to_cols.get(col_name, None)
    
class OrgList(list):
  def __init__(self):
    self.org_list = []
    # self.db_name = db_name
    # self.enz_list = [] если юзаем - заполняем в fill_from_db_rows!
    # self.su_list = []
    self.enz_ids = []
    self.su_names_union = set()
    self.su_names_isect = set()
    
  def set_org_list(self, org_list):
    self.org_list.clear()
    self.enz_ids.clear()
    for org in org_list:
      if type(org).__name__ == 'Organism':
        for enz in org.enz_list:
          if type(enz).__name__ == 'Enzyme':
            self.su_names_union.update(enz.su_names_union)
            self.enz_ids.append(enz.id)
        self.org_list.append(org)
    self._mk_su_names_isect() #only after adding all organisms!
         
  def fill_from_db_rows(self, db_rows, org_attr_names = [], enz_attr_names = [], 
                                                            su_attr_names = []):
    cur_org_id, cur_enz_id, org, enz, su = None, None, None, None, None
    # all_cols_names = oac_names + eac_names + sac_names - not used because 
    # row can lack enzyme info if we output only organisms
    for row in db_rows:
      if sf.check_dict_keys(enz_attr_names + ['enz_id', 'enz_name'], row):
        new_enz_id = row['enz_id']
        if cur_enz_id != new_enz_id:
          if cur_enz_id: # not None = here's an enzyme created and filled in
            org.add_enzyme(enz) # add last created enzyme to current org
            self.enz_ids.append(enz.id)
          cur_enz_id = new_enz_id # change current enzyme
          enz = Enzyme(new_enz_id, row['enz_name'], cur_org_id) 
          enz.fill_attr(enz_attr_names, row)
        #if there's enzyme - we can add a subunit (if any)
        if sf.check_dict_keys(su_attr_names + ['su_id', 'su_name', 'su_seq'], 
               row):
          su = Subunit(row['su_id'], row['su_name'], row['su_seq'], cur_enz_id)
          if not su.name in self.su_names_union:
            self.su_names_union.add(su.name)
        su.fill_attr(su_attr_names, row)
        enz.add_subunit(su)
      if sf.check_dict_keys(org_attr_names + ['org_id', 'org_name'], row):
        new_org_id = row['org_id']
        if cur_org_id != new_org_id:# TODO: check ORDER BY org_id!
          if cur_org_id: # not None = here's an organism created and filled in
            self.org_list.append(org) # add last created org to org list
          cur_org_id = new_org_id # start new org
          org = Organism(new_org_id, row['org_name'])
          org.fill_attr(org_attr_names, row)
    if type(org).__name__ == 'Organism':
      if type(enz).__name__ == 'Enzyme': #there were 'enzymes' table rows too
        # self.enzymes.append(enz
        org.add_enzyme(enz) # last enz isn't added: no new_enz_id was met
        self.enz_ids.append(enz.id)
      self.org_list.append(org) # last org isn't added: no new_org_id was met!
    self._mk_su_names_isect() # make the intersection
      
  def _mk_su_union():
    pass
      
  def _mk_su_names_isect(self):
    self.su_names_isect = self.su_names_union
    for org in self.org_list:
      for enz in org.enz_list:
        self.su_names_isect = self.su_names_isect & enz.su_names_union
  
class DbObj:
  def __init__(self, db_name = '', db_descr = ''):
    self.db_name = db_name
    self.db_descr = db_descr
    self.attr_col_descr_list = AttrColDescrList()
    self.org_list_obj = OrgList()
      
  def set_from_db_rows(self, db_rows, attr_rows = None):
    if attr_rows:
      if type(attr_rows).__name__  == 'str':
        # print('cannot set attribute columns description<br>')
        return ['Cannot set attributes in DbObj: ' + attr_rows]
      elif type(attr_rows).__name__ == 'AttrColDescrList':
        # print('got ready attribute columns description<br>')
        self.attr_col_descr_list = attr_rows
      else:
        self.attr_col_descr_list.fill_from_attr_rows(attr_rows)
    if type(db_rows).__name__ == 'str':
      return ['Cannot set organisms, enzymes and subunits in DbObj: ' + db_rows]
    o_names = self.attr_col_descr_list.get_table_col_names('organisms')
    e_names = self.attr_col_descr_list.get_table_col_names('enzymes')
    s_names = self.attr_col_descr_list.get_table_col_names('subunits')
    self.org_list_obj.fill_from_db_rows(db_rows, o_names, e_names, s_names)
    
  def get_attr_col_descrs(self):
    return self.attr_col_descr_list.all_cols
    
  def get_org_list(self):
    return self.org_list_obj.org_list
    # for org in org_list:
      # if type(org).__name__ == 'Organism':
        # self.org_list.append(org)
        
  def get_enz_ids(self):
    return sorted(self.org_list_obj.enz_ids)
        
    