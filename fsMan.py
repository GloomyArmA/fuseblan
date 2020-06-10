#fsMan.py
import os
import shutil
from time import ctime # to get time when file was last modified 

dbs_dir = 'databases'

def check_fs_name(fs_name):
  #test whether db_name is correct for file system
  return True

def get_db_folder(db_name):
  #test db_name and return db path
  return os.path.join(dbs_dir, db_name) if check_fs_name(db_name) else ''
  
def get_al_path(db_name):
  db_name = get_db_folder(db_name)
  return os.path.join(db_name, 'alignments')
  
def get_seq_path(db_name):
  db_name = get_db_folder(db_name)
  return os.path.join(db_name, 'su_seqs')
  
def get_full_path(path, f_name):
  return os.path.join(path, f_name)
  
def mk_paths(db_name):
  paths = []
  paths.append(get_db_folder(db_name)) #path to db dumps
  paths.append(get_al_path(db_name)) #path to alignments
  paths.append(get_seq_path(db_name)) #path to subunit sequences
  return paths
  
  
def delete_folder(folder):
  if not os.path.exists(folder):
    return ['Cannot find "' + folder + '" folder to delete it']
  try:
    shutil.rmtree(folder)
    return []
  except Exception as e:
    return [str(e)]
    
def delete_db_folder(db_name):
  db_folder = get_db_folder(db_name)
  return delete_folder(db_folder)
    
def create_db_folder(db_name):
  try:
    if not os.path.exists(dbs_dir):
      os.mkdir(dbs_dir)
    for path in mk_paths(db_name):
      os.mkdir(path)
      if not os.path.exists(path):
        return ['failed to create folder' + path]
  except Exception as e:
    return ['got exception creating folders' + str(e)]
  return []
  
def check_file_action(action):
  return True if action in list('rwxabt+') else False

def mk_db_dump_f_name(db_name):
  return os.path.join(get_db_folder(db_name), db_name + '_dump.xml')
  
def open_db_dump_file(db_name, action):
  return open(mk_db_dump_f_name(db_name), action)
  
def mk_su_seq_fasta_name(db_name, su_name):
  return os.path.join(get_seq_path(db_name), su_name + '.fasta')
  
def open_su_seq_fasta(db_name, su_name, action):
  f_name = mk_su_seq_fasta_name(db_name, su_name)
  return open(f_name, action), f_name
  
def get_db_dump_info(db_name):
  dump_f_name = mk_db_dump_f_name(db_name)
  if os.path.exists(dump_f_name):
    change_time = os.path.getmtime(dump_f_name)
    return dump_f_name, ctime(change_time)
  return '', 'No dump file'
    
def open_file(path, f_name, action):
  #action is 'r','w' or 'rw'
  return open(os.path.join(path, f_name), action)