#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

import sharedClasses as sc 
import sharedHtml as sh
import sharedFuncs as sf
import dbFace as df
import fsMan as fs
import faster 
import cgi 
import cgitb

def mk_seq_src_files(db_name, su_name_to_fasta_recs, su_name_to_fasta):
  for su_name, fasta_recs in su_name_to_fasta_recs.items():
    # f_name = fs.get_full_path(fs.get_seq_path(db_name), su_name + '.fasta')
    f_name = faster.mk_su_seq_fasta(db_name, su_name, fasta_recs)
    su_name_to_fasta[su_name] = f_name
        
def mk_su_name_to_fasta_recs(org_list_obj):
  su_name_to_fasta_recs = dict()
  for su_name in org_list_obj.su_names_union:
    su_name_to_fasta_recs[su_name] = []
  for org in org_list_obj.org_list:
    for enz in org.enz_list:
      for su in enz.su_list:
        f_rec = faster.FullSeqData(org.id, org.name, enz.id, enz.name, 
                               su.id, su.name, su.su_seq)
        su_name_to_fasta_recs[su.name].append(f_rec)
  return su_name_to_fasta_recs
  
def mk_data_form(db_name, id_set, filter_str, org_list, content):
  data_form = '<form enctype="multipart/form-data" id = "metadata" ' + \
              'method = "POST" >\n '
  data_form += sh.mk_db_name_field(db_name)
  data_form += sh.mk_id_set_field('enz_id', id_set)
  data_form += sh.mk_hidden_field('filter_str', filter_str)
  data_form += sh.mk_hidden_field('su_names', 
                                  str(sorted(org_list.su_names_isect)))
  data_form += content
  data_form += sh.mk_submit_btn('add fused alignment from files loaded above',
                                'alMan.py')
  data_form += '</form> \n'
  return data_form
  
def mk_content(filter_str, org_list, su_name_to_fasta):
  html = '<font class = "h3"> Filters checked to choose the enzymes: ' + \
         '<font color = "#0F0">' + filter_str + \
         '</font></font><br>\n'
  html += '<font class = "h3"> Chosen enzymes have subunits: ' + \
         '<font color = "#0F0">' + str(sorted(org_list.su_names_union)) + \
         '</font></font><br>\n'
  html += '<font class = "h3"> Subunits shared by every enzyme: ' + \
          '<font color = "#0F0">' + str(sorted(org_list.su_names_isect)) + \
          '</font></font><br>\n'
  html += '<div class = "content_frame">\n<div class = "table_holder">\n'
  headers = ['subunit', 'fasta with sequences', 'fasta with alignment',
             'alignment blocks markup']
  html += '<table class = "viewer"><tr><td>' + '</td><td>'.join(headers) + \
          '</td></tr>\n'
  for su_name in sorted(su_name_to_fasta.keys()):
    f_name = su_name_to_fasta[su_name]
    al_field = '<input type = "file" name = "al_' + su_name + '">'
    bm_field = '<input type = "text" name = "bm_' + su_name + \
               '" placeholder = "10-17;... (first-last block col number)">'
    common_str = '<td>' + su_name + '</td><td><a href = "' + f_name + '">' + \
            su_name + '.fasta </a></td><td>'
    if su_name in org_list.su_names_isect: #hillight table row and show "add 
      #file" button if subunit is shared by all enzymes:
      html += '<tr class = "active_green">' + common_str + al_field + \
              '</td><td>' + bm_field 
    else:
      html += '<tr>' + common_str + '</td><td></td>'
    html += '</td></tr>\n'
  html += '</table>\n</div>\n</div>\n'
  return html
  
def get_filter_str(post_data, id_set):
  if id_set:
    return post_data.getvalue('filter_vals_ta', '').replace('\n', ' | ')
  return 'no enzymes with applied filters were checked, showing all the enzymes'
  
post_data = cgi.FieldStorage()
page_name, label, content, html = 'getSuSeqLoadAl.py', [], '', ''
su_name_to_fasta, org_list = dict(), sc.OrgList()
if not post_data:
  html = sh.mk_page_header(page_name, no_post_data = True)
else:
  id_set = sh.get_id_set_from_cb(post_data, 'enzymes')
  filter_str = get_filter_str(post_data, id_set)
  # if no id_set is provided - output has all the enzymes
  wc = sf.get_where_id_case(id_set, 'enzymes', True)
  db_name = sh.get_db_name(post_data)
  if db_name:
    db_link, db_cursor = df.get_link_and_cursor(db_name)
    if db_cursor:
      db_rows = df.get_db_rows(db_cursor, ' WHERE ' + wc if wc else '')
      org_list.fill_from_db_rows(db_rows)
      label = ' of ' + str(len(org_list.enz_ids)) + ' enzymes in ' + \
               str(len(org_list.org_list)) + ' organisms'
      #get subunit sequences:
      su_name_to_fasta_recs = mk_su_name_to_fasta_recs(org_list)
      #make fasta-files with subunit sequences:
      mk_seq_src_files(db_name, su_name_to_fasta_recs, su_name_to_fasta)
      #make page content: table with subunits, files and description
      content = mk_content(filter_str, org_list, su_name_to_fasta)
      #wrap content in data_form with post data for alignment manager:
      content = mk_data_form(db_name, id_set, filter_str, org_list, content)
  html = sh.mk_page_header(page_name, page_label = label) + content

print(html)