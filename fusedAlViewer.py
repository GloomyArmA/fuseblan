#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

# import re
import fusedAlClasses as fac
# import fusedAlXmler as fax
import cgi 
import cgitb
#import srcAndAlMaker as saam
# import sharedVars as sv
import sharedFuncs as sf
import sharedClasses as sc
import sharedHtml as sh
import htmlClasses as hc
import dbFace as df
import filterClasses as fc
import filterHtml as fh

panel_height = 300
         
class ViewerData:
  def set_filtered_enz_ids(self, db_cursor):
    if type(self.filter_set).__name__ != 'FilterSet':
      return
    query = 'SELECT e.enz_id FROM `enzymes` e INNER JOIN organisms o ' + \
            'ON e.org_id = o.org_id'
    eid_wc = sf.get_where_id_case(self.f_al.enz_id_set, 'enzymes', True)
    f_wc = self.filter_set.get_db_query_filter()
    if eid_wc and f_wc: 
      wc = ' WHERE ' + eid_wc + ' AND ' + f_wc
      enz_id_rows = df.send_query(db_cursor, query + wc)
      for row in enz_id_rows:
        self.filt_enz_id_set.add(row['enz_id'])
        
  def set_org_id_set(self):
    for ed in self.enz_id_to_enz_descr.values():
      self.org_id_set.add(ed.org_id)
        
  def set_fused_al_enz_names_and_filters(self, db_cursor, post_data):
    self.f_al.set_from_db(db_cursor, self.al_id)
    if self.f_al.enz_id_set:
      self.enz_id_list = sorted(self.f_al.enz_id_set)
      self.enz_id_to_enz_descr = sf.get_enz_id_to_enz_descr(db_cursor, 
                                                    self.f_al.enz_id_set)
      #set up org_id_set from enz_id_to_enz_descr:
      self.set_org_id_set()
      #make db_obj to get attr cols for making filters:
      db_obj = sc.DbObj()
      attr_rows = df.get_attr_rows(db_cursor)
      # fill attribute columns description list to set organisms and filters:
      db_obj.attr_col_descr_list.fill_from_attr_rows(attr_rows) 
      # make filters to filter rows obtained from database
      self.filter_set = fc.FilterSet(db_cursor, post_data, db_obj, 
                                     self.f_al.enz_id_set, self.org_id_set)
                                     
  def set_block_markup(self, post_data):
    for sn in self.f_al.su_names:
      al_length = self.f_al.sn_to_al[sn]
      bm_str = post_data.getvalue('bm_' + sn, '')
      bm = fac.get_block_markup(bm_str, al_length)
      if True in bm: #some of bm items are True if markup is correct
        self.f_al.sn_to_bm[sn] = bm
        
  def save_block_markup(self, db_cursor):
    for sn, bm in self.f_al.sn_to_bm.items():
      bm_str = fac.bm_to_bm_str(bm)
      query = 'UPDATE `al_su_data` SET block_markup = "' + bm_str + \
            '" WHERE al_id = ' + str(self.al_id) + ' AND su_name = "' + sn + '"'
      result = df.send_query(db_cursor, query)
    self.save_bm = False #to avoid of constant rewriting with each page load
    
  def __init__(self, post_data):
    self.f_al, self.enz_id_to_enz_descr = fac.FusedAlignment(), dict()
    self.filt_enz_id_set , self.filter_set = set(), None
    self.org_id_set, self.enz_id_list = set(), []
    self.db_name = sh.get_db_name(post_data)  
    self.al_id = sf.try_val_to_int(post_data.getvalue('al_id', ''))
    #get ref id to enumerate alignment position as in reference enzyme:
    self.ref_id = sf.try_val_to_int(post_data.getvalue('ref_id', ''))
    #get view mode to show alignments as blocks and spacers or as sequences
    self.show_blocks = eval(post_data.getvalue('show_mode','False'))
    #get markup checkboxes:
    self.set_bm = post_data.getvalue('set_bm', False)
    self.save_bm = post_data.getvalue('save_bm', False)
    #set self.su, self.pos and self.aac_name to split by aac:
    if self.al_id and self.db_name:
      db_link, db_cursor = df.get_link_and_cursor(self.db_name)
      if db_cursor:
        self.set_fused_al_enz_names_and_filters(db_cursor, post_data)
    #obtain filtered enzymes identifiers (if any) for further split and analyse:
        self.set_filtered_enz_ids(db_cursor)
    #change blocks markups on ones from post if "set_bm" is checked:
        if self.set_bm:
          self.set_block_markup(post_data)
    #save blocks markups to db if "save_bm" is checked then uncheck "save_bm":
        if self.save_bm:
          self.set_block_markup(post_data)
          self.save_block_markup(db_cursor)

  def get_ref_id_field(self):
    return sh.mk_select('ref_id', self.enz_id_list, self.enz_id_to_enz_descr, 
                         selected_set = {self.ref_id})
                        
  def get_show_mode_field(self):
    show_modes = {'True':'blocks and spacers', 'False':'sequence'}
    return sh.mk_select('show_mode', ['True', 'False'], show_modes,
                         selected_set = sf.to_set(str(self.show_blocks)))
                               
  def get_sn_to_bm_field(self):
    sn_to_bm_field = dict()
    for sn, bm in self.f_al.sn_to_bm.items():
      field = '<input type = "text" size = "80" name = "bm_' + sn + \
              '" value = "' + fac.bm_to_bm_str(bm)
      field += '">' #if self.set_bm else '" readonly>'
      sn_to_bm_field[sn] = field
    return sn_to_bm_field
  
  def get_set_bm_checkbox_html(self):
    # js = ' onclick = "setEnableChBox(this, \'' + db_descr_ta + '\')">'
    return sh.mk_checkbox('set_bm', 'set another markup', self.set_bm, js = '')
    
  def get_save_bm_checkbox_html(self):
    return sh.mk_checkbox('save_bm', 'save markup to db', self.save_bm, js = '')
    
  def get_al_filter_str_field_html(self):
    html = 'Filters used to get fused alignment: <br>'
    html += sh.mk_textarea("al_filter_ta", 2, 40, self.f_al.filter_str)
    return html
    
  def get_split_filter_str_field_html(self):
    sp_fil_str = '\n'.join(self.filter_set.get_filters_values())
    html = 'Filters used to split alignment: <br>'
    html += sh.mk_textarea("split_filter_ta", 2, 40, sp_fil_str)
    return html
    
  def get_al_enz_id_set_field_html(self):
    html = 'All alignment enzymes id set: <br>'
    html += sh.mk_textarea("al_enz_ids", 2, 30, self.enz_id_list)
    return html
    
  def get_split_enz_id_set_field_html(self):
    html = 'Filtered enzymes id set: <br>'
    html += sh.mk_textarea("filt_enz_ids", 2, 30, sorted(self.filt_enz_id_set))
    return html
                            
def mk_options_panel(v_data):  
  html = '<table>'
  html += '<tr><td title = "select reference enzyme for alignment postitions">'
  html += 'Reference enzyme: ' + v_data.get_ref_id_field() + '</td></tr>\n'
  html += '<tr><td title = "show alignment as blocks and spacers or as sequence">'
  html += 'Show mode: ' + v_data.get_show_mode_field()
  html += v_data.get_set_bm_checkbox_html() + v_data.get_save_bm_checkbox_html()
  html += '</td></tr>\n <tr><td>'
  html += sh.mk_submit_btn('Apply options', 'fusedAlViewer.py')
  html += '</td></tr>\n</table>\n'
  return html

def mk_block_markup_panel(v_data):
  html = '<div style = "height: 150px; overflow:scroll">\n '
  html += 'Block markups: (format: 10-20;54-67;... )<br>\n'
  html += '<table>'
  for sn, bm_field in v_data.get_sn_to_bm_field().items():
    html += '<tr><td>'+ sn + '</td><td>' + bm_field + '</td></tr>\n'
  html += '</table></div>\n'
  return html
  
# def mk_field_set(label, content):
  # return '<fieldset> <legend> ' + label + '</legend>' + content + '</fieldset>'
  
def mk_filters_panel(v_data):
  html = '<table>'
  html += '<tr><td>' + v_data.get_al_filter_str_field_html() + '</td>\n'
  html += '<td>' + v_data.get_al_enz_id_set_field_html() + '</td>\n'
  html += '<td>' + v_data.get_split_filter_str_field_html() + '</td>\n'
  html += '<td>' + v_data.get_split_enz_id_set_field_html() + '</td></tr>\n'
  html += '</table>\n'
  return html

def mk_data_form(v_data, content):# opt_panel, bm_panel, filt_panel):
  html = '<form id = "metadata" method = "POST">'
  html += sh.mk_db_name_field(v_data.db_name)
  html += sh.mk_hidden_field('al_id', str(v_data.al_id))
  html += '<table class = "form_holder"><tr>' #viewer options
  html += '<td>' + mk_options_panel(v_data) + '</td>\n'
  html += '<td>' + mk_block_markup_panel(v_data) + '</td>'
  html += '</tr>\n</table>\n' #viewer options closed
  html += '<table class = "form_holder">' 
  html += '<tr><td>' + mk_filters_panel(v_data) + '</td></tr>\n'
  html += '</table>\n' #form_holder closed
  html += '<table class = "form_holder"><tr><td>'
  # html += fh.mk_filter_form(v_data.filter_set, 'Set filters to get split ids', 
          # 'Load filtered ids','fusedAlViewer.py', 'metadata', False, False)
  # html += '</td><td>Source of split enzymes set:<br>'
  # html += sh.mk_select('split_source', ['filters', 'checkboxes', 'su_pos_aac'])
  # html += sh.mk_submit_btn('Split with polinomial probability', 
          # 'splitAnProb.py')
  # html += sh.mk_submit_btn('Split and analyse with Shannon entropy', 
                           # 'splitAnShan.py')
  html += sh.mk_submit_btn('Split and analyse',  'splitAn.py')
  html += '</td></tr></table>\n'
  html += content
  html += '</form>\n'
  return html

      
def mk_name_table_row(enz_descr):
  return '<tr><td>' + sh.mk_id_checkbox(enz_descr.enz_id, 'enzymes') + ' #' + \
       str(enz_descr.enz_id) + '</td><td>' + enz_descr.name_str + '</td></tr>\n'
       
def mk_al_cell(aac, bg_clr, fg_clr, su_name = '', ref_aac = None):
  aac_html = aac.get_html()
  html = '<td title = "' + aac.get_title(su_name, ref_aac) + \
         '" bgcolor = "' + bg_clr + '">'
  if aac_html:
    html += '<font color = "' + fg_clr + '">' + aac_html + '</font>'
  return html + '</td>'
  
def mk_al_seq_row(aac_row, bg_clr, fg_clr, su_name, ref_aac_row = None):
  html, al_length = '', len(aac_row)
  if ref_aac_row and len(ref_aac_row) == al_length:
    for i in range(0, len(aac_row)):
      html += mk_al_cell(aac_row[i], bg_clr, fg_clr, su_name, ref_aac_row[i])
  else:
    for aac in aac_row:
      html += mk_al_cell(aac, bg_clr, fg_clr, su_name)
  return html
  
def mk_block_row(bl_sp_row, bg_clr, fg_clr, su_name, ref_bl_sp_row = None):
  html, bs_length = '', len(bl_sp_row)
  if ref_bl_sp_row and len(ref_bl_sp_row) == bs_length:
    for i in range(0, bs_length):
      html += mk_al_cell(bl_sp_row[i], bg_clr, fg_clr, su_name, 
                                                   ref_bl_sp_row[i])
  else:
    for item in bl_sp_row:
      html += mk_al_cell(item, bg_clr, fg_clr, su_name)
  return html
  
def mk_al_seq_table_rows(v_data, su_colors):
  as_tr = ''
  sn_to_ref_aac_row = v_data.f_al.get_sn_to_aac_row(v_data.ref_id)
  for enz_id in v_data.enz_id_list:
    as_tr += '<tr>'
    for sn in v_data.f_al.su_names:
      bc, fc = su_colors.get_bg_color(sn), su_colors.get_fg_color(sn)
      aac_row = v_data.f_al.sn_to_ars[sn].get(enz_id, [])
      ref_aac_row = sn_to_ref_aac_row.get(sn, None)
      as_tr += mk_al_seq_row(aac_row, bc, fc, sn, ref_aac_row)
    as_tr += '</tr>\n'
  return as_tr
    
def mk_block_table_rows(v_data, su_colors):
  bs_tr = ''
  sn_to_brs = v_data.f_al.get_su_name_to_block_rows()
  sn_to_ref_bl_sp_row = dict()
  if v_data.ref_id: #fill in reference bl_sp_row
    for sn, enz_id_to_bl_sp_row in sn_to_brs.items(): 
      sn_to_ref_bl_sp_row[sn] = enz_id_to_bl_sp_row.get(v_data.ref_id, None)
  for enz_id in v_data.enz_id_list:
    bs_tr += '<tr>'
    for sn in v_data.f_al.su_names:
      bc, fc = su_colors.get_bg_color(sn), su_colors.get_fg_color(sn)
      bl_sp_row, ref_bl_sp_row = sn_to_brs[sn][enz_id], sn_to_ref_bl_sp_row[sn]
      bs_tr += mk_block_row(bl_sp_row, bc, fc, sn, ref_bl_sp_row)
    bs_tr += '</tr>\n'
  return bs_tr

def mk_content(viewer_data):
  vd, view_panel = viewer_data, hc.Panel(panel_height)
  names_tbl = su_al_tbl = '<table class = "viewer">'
  names_header, su_al_header, ct = '', '', '</table> \n'
  su_colors = hc.BgFgHtmlColor(vd.f_al.su_names, contrast_delta = 120)
  for enz_id in vd.enz_id_list:
    names_tbl += mk_name_table_row(vd.enz_id_to_enz_descr[enz_id])
  # if vd.show_blocks:
    # su_al_tbl += mk_block_table_rows(vd, su_colors)
  # else:
    # su_al_tbl += mk_al_seq_table_rows(vd, su_colors)
  names_header = str(len(vd.enz_id_list)) + ' enzymes' 
  su_al_header = '<b>{subunit : alignment length}</b>: &nbsp;&nbsp;' + \
                 str(vd.f_al.sn_to_al)
  view_panel.add_sect(hc.PanelSect(names_header, names_tbl + ct, 15))
  # if len(vd.enz_id_list) < 100:
  view_panel.add_sect(hc.PanelSect(su_al_header, su_al_tbl + ct, 84))
  return view_panel.get_html()
  
cgitb.enable()
post_data = cgi.FieldStorage()
page_name, status, content, label, html = 'fusedAlViewer.py', [], '', '', ''
if not post_data: 
  html = sh.mk_page_header(page_name, no_post_data = True)
  # html += '<form action = "fusedAlViewer.py" method = "POST" enctype="multipart/form-data">'
  # html += '<input type = "file" name = "xml_source">'
  # html += '<input type = "submit" value = "view alignment">'
  # html += '</form>'
else:
  vd = ViewerData(post_data) #gather db_name, al_id, filters, etc. from post
  content = mk_content(vd)
  label = ' for database ' + vd.db_name
  #wrap content in data_form with post data for alignment manager:
  content = mk_data_form(vd, content)
  html = sh.mk_page_header(page_name, status, label) + content

print(html)
