#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

# from contextlib import closing
# import os # 
# from copy import deepcopy #to fill db_info_list
import cgi 
import cgitb
import fusedAlClasses as fac
import faster as fst
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

#input: db_name - required, set of fasta alignment files with description - if
#adding new alignment (called from getSuSeqAlLoad)
#output for other scripts: actions - if any action chosen to perform, al_id - 
#which alignment to use for action

def mk_al_radio(al_id):
  return '<input type = "radio" name = "al_id" value = "' + \
         str(al_id) + '" title = "check to choose alignment">'
         
def add_new_alignment(post_data, db_cursor, enz_id_set):
  f_al = fac.FusedAlignment()
  #check for loaded alignment fasta, add them and their subunits to f_al:
  su_names, sn_to_al = [], dict()
  for sn in eval(post_data.getvalue('su_names', [])): 
    al_fasta = post_data.getvalue('al_' + sn, None)
    if al_fasta: 
      su_names.append(sn)
      sn_to_al[sn] = al_fasta
  filter_str = post_data.getvalue('filter_str', '')
  if f_al.set_al_info(enz_id_set, filter_str, su_names): 
    for sn in su_names:
      bm_str = post_data.getvalue('bm_' + sn)
      # make list of FullSeqData objeects from fasta content in html field:
      fsd_list = fst.parse_fasta_to_fsd_list(sn_to_al[sn])
      if fsd_list and type(fsd_list[0]).__name__ == 'FullSeqData':
        #check does the subunit of alignment fasta loaded correspond to 
        #current subunit, and if there a sequences given (=have al_length):
        al_length = len(fsd_list[0].seq)
        if fsd_list[0].get_su_name() == sn and al_length: #all seems to be ok
          f_al.add_su_data(sn, al_length, bm_str) #fill in subunit data
          for fsd in fsd_list: #fill in aligned subunit sequences:
            f_al.add_al_seq(sn, fsd.get_enz_id(), fsd.seq)
    return f_al.add_to_db(db_cursor)
  return ['New alignment hasn\'t been added']
  
  
def get_al_rows(db_cursor):
  query = "SELECT * FROM `al_info` ORDER BY al_id"
  return df.send_query(db_cursor, query)

def mk_al_anchor(db_name, al_id, ctime_str):  
  al_id = sf.try_val_to_int(al_id)
  if al_id:
    al_name = str(al_id) + ' (' + ctime(sf.try_val_to_float(ctime_str)) + ')'
    return '<a href = "fusedAlViewer.py?al_id=' + str(al_id) + '&db_name=' + \
           db_name + '">' + al_name + '</a>'
  return ''

def get_enz_names(enz_id_set, enz_id_to_enz_descr):
  enz_names = []
  try:
    for e_id in enz_id_set:
      enz_names.append(str(enz_id_to_enz_descr[e_id]))
  except Exception as e:
    return ['parsing enzyme names failed:' + str(e)]
  return enz_names
  
def mk_data_form(db_name, content):
  data_form = '<form name = "metadata" id = "metadata">\n '
  data_form += sh.mk_db_name_field(db_name)
  data_form += content
  data_form += '</form>'
  return data_form

def mk_content(db_name, al_rows, enz_id_to_enz_descr, ):
  html = '<div class = "content_frame"><div class = "table_holder">\n'
  header = ['alignment (click to view)', 'enzyme id set', 
            'enzymes description', 'applied filters', 'subunit set']
  html += '<table class = "viewer"><tr><td>' + '</td><td>'.join(header) + \
          '</tr></tr>\n'
  for row in al_rows:
    al_id, ctime_str = row.get('al_id',''), row.get('ctime', '')
    al_title = mk_al_anchor(db_name, al_id, ctime_str)
    if al_title: #make alignment table row
      enz_id_set = eval(row.get('enz_id_set', 'set()'))
      enz_names = get_enz_names(enz_id_set, enz_id_to_enz_descr) 
      html += '<tr><td>'+ al_title + '</td>'
      html += '<td><textarea cols = "20" rows = "3" readonly>' + \
              str(sorted(enz_id_set)) + '</textarea></td>'
      html += '<td><textarea cols = "50" rows = "3" readonly>' + \
              ',\n'.join(enz_names) + '</textarea></td>'
      html += '<td><textarea cols = "20" rows = "3" readonly>' + \
              str(row.get('filter_set')) + '</textarea></td>'
      html += '<td>' + str(row.get('su_names')) + '</td>'
      html += '</td></tr>\n'
  html += '</table>\n</div>\n</div>\n'
  return html

post_data = cgi.FieldStorage()
page_name, label, content, html, status = 'alMan.py', [], '', '', []
if not post_data:
  html = sh.mk_page_header(page_name, no_post_data = True)
else:
  db_name = sh.get_db_name(post_data)  
  if db_name:
    db_link, db_cursor = df.get_link_and_cursor(db_name)
    if db_cursor:
      id_set = sh.get_id_set_from_post(post_data, 'enzymes')
      if id_set:
        status = add_new_alignment(post_data, db_cursor, id_set)
      al_rows = get_al_rows(db_cursor)
      enz_id_to_enz_descr = sf.get_enz_id_to_enz_descr(db_cursor)
      content = mk_content(db_name, al_rows, enz_id_to_enz_descr)
      label = ' for database ' + db_name
      # #wrap content in data_form with post data for alignment manager:
      content = mk_data_form(db_name, content)
  html = sh.mk_page_header(page_name, status, label) + content

print(html)

