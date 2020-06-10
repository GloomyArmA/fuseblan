#sharedVars.py
import os

header_path = 'header.html'

na_vals = ['None', 'NA', '', ' - ', 'Null', 'NULL', 'NAN']

main_tables = ["organisms", "enzymes", "subunits"] # ordered by hierarchy

db_name_prefix = 'fb_'

#which db to use and how to connect:
db_params = {
  'user': 'fuseblan',
  'passwd':'s1nthases'
  }

  
attr_sect_width = 40


al_db_cols = [
  'al_id',
  'job_id',
  'su_list',
  'enz_id_list_hash'
  ]
  
#alignments folder structure:
#Aligner executable file(s) is(are) in the root of aligner_dir. 
#Each performaed alignment uses data in folder having name made of current 
#datetime (job_id variable). All source fasta files and ready alignments
#are named as subunits aligned there and have a concordant suffixes
#path to make alignments in 'job_dir':
aligner_dir = 'alignerData' 
#path to aligner, left for future usage
aligner_soft = os.path.join(aligner_dir,'muscle.exe') 
current_job_id = 'Thu_Oct_24_21-12-33_2019'
al_file_suffix = '_al.fasta'

sh_entropy_threshold = -0.5


    

    

  
 
