import re
from sys import argv
from contextlib import closing

# procedure: 
# get id:=name\tvalue db-file and name\tvalue data-file.
# for each name in db-file:
# look for similar (having at least pair of the same words) name
# get the value of found name and assign it to df-file name
# similarity: 
# in each data-name look for the first word of db-name.
# if found, write down record with this name to db-name-matches
# in each record 
# anyway at least two words have to match, and that words exclude "candidatus"

id_name_spl = ':='
name_val_spl = '\t'
skip_words = ['endosymbiont', 'candidatus']
skip_vals = ['NA', 'none', 'not indicated', '']

def get_name_words(raw_name):
  n_parts = re.split(r'\W', raw_name) # break raw_name on words
  name_words = set() #set() to avoid of 'Listeria Listeria sp.' double matches
  for part in n_parts:#leave only words consist of letters:
    if part.isalpha() and not (part in skip_words): 
      name_words.add(part)
  return list(name_words)

class DbNameVal:
  def __init__(self, rec):
    self.id, self.name, self.name_words, self.val = '', '', [], ''
    rec = rec.replace('\r', '').replace('\n','').split(name_val_spl)
    if len(rec) == 2:
      id_name = re.split(id_name_spl, rec[0].strip())
      if len(id_name) == 2:
        id = id_name[0].replace(' ', '')
        if id.isnumeric():
          self.id = id
          self.name = id_name[1]
          self.name_words = get_name_words(self.name)
          self.val = rec[1]
  
  def get_record(self):
    return self.id + id_name_spl + self.name + name_val_spl + self.val
    
class DataNameVal:
  def __init__(self, rec):
    self.name, self.name_words, self.val = '', [], ''
    rec = rec.replace('\r', '').replace('\n','').split(name_val_spl)
    if len(rec) == 2:
      self.name, self.val = rec[0], rec[1]
      #to avoid of 'Listeria Listeria sp.' double matches:
      self.name_fixed = ' '.join(get_name_words(self.name))

      
def assign_val(changed_list, db_name_val, data_name_val_list):
  cur_max, max_matches = 2, []
  #regexp to look for matches to whole words db-name consist of:
  rexp = '\\b' + '\\b|\\b'.join(db_name_val.name_words) + '\\b'
  # print('rexp:', rexp)
  for dnv in data_name_val_list:
    match_num = len(re.findall(rexp, dnv.name_fixed))
    if match_num > cur_max: #change cur_max, delete all items of less length
      cur_max = match_num
      max_matches.clear()
    if match_num == cur_max: #works either match_num changed or not
      max_matches.append(dnv)
  #now data with best matching names are in list. How to choose the proper 
  #value? just take first record having proper value
  for dnv in max_matches:
    if dnv.val and not (dnv.val in skip_vals):
      print(db_name_val.name, ' matching name: ', dnv.name)
      print('  old value: ', db_name_val.val, ', new value:', dnv.val)
      db_name_val.val = dnv.val
      changed_list.append(db_name_val)
  
def read_file(f_name, obj_list, obj_class):
  if obj_class not in ['DbNameVal', 'DataNameVal']:
    return
  with closing(open(f_name, 'r')) as f:
    for rec in f.readlines():
      obj = eval(obj_class + '(rec)')
      if obj.name:
        obj_list.append(obj)
    
        
db_inv_list, data_nv_list, changed_list  = [], [], []
db_file, data_file, dest_file = argv[1], argv[2], argv[3]

read_file(db_file, db_inv_list, 'DbNameVal')
read_file(data_file, data_nv_list, 'DataNameVal')

for db_inv in db_inv_list:
  # print('db object: ', db_inv.name_words, db_inv.val)
  assign_val(changed_list, db_inv, data_nv_list)
  
with closing(open(dest_file, 'w')) as df:
  for db_inv in changed_list:
    df.write(db_inv.get_record() + '\n')
# print('\n'.join([o.get_record() for o in db_inv_list]))
    
