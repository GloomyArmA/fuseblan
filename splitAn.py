#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

import splitAnClasses as sac
import cgi 
import cgitb
import dbFace as df
import sharedFuncs as sf
import sharedClasses as sc
import sharedHtml as sh
import htmlClasses as hc
import filterClasses as fc
import filterHtml as fh

class SplitData:
  def set_su_pos_aac_split_ids(self, post_data):
    # get select name from radio consist of su and pos separated with '_' then
    # get aac_name from select with su_pos name:
    select_name = post_data.getvalue('su_pos', '')
    su_pos = select_name.split('_')
    if len(su_pos) == 2 and su_pos[1].isnumeric():
      #obtain aac from select select_name and write out data to su_pos_aac:
      aac = post_data.getvalue(select_name, '')
      self.su_pos_aac = [su_pos[0], su_pos[1], aac]
      #fill in split_ids:
      self.split_ids = self.split.get_split_ids_from_su_pos_aac(su_pos[0], 
                                                                su_pos[1], aac)
      self.split_crit_str = 'Subunit:'+ self.su_pos_aac[0] + '\n' + \
                            'Position:' + self.su_pos_aac[1] + '\n' + \
                            'Aminoacid:' + self.su_pos_aac[2]
    if not self.split_ids:
      self.split_crit_str = 'subunit, position and aminoacid aren\'t defined'
    
  def set_split_ids_and_crit(self, post_data):
    split_source = post_data.getvalue('split_source', '')
    #there are three enz_ids sources available: current split, filtered
    #enzyme ids, enzymes with specified aac in pos of subunit.
    if split_source == 'current_split': #split_ids are in 'split_ids' 
      #hidden field, split criteria info is in split_crit_ta:
      self.split_ids = eval(post_data.getvalue('split_ids', '[]'))
      self.split_crit_str = post_data.getvalue('split_crit_ta', '').replace('\n', '')
      # self.split_source = 'current_split'
    elif split_source == 'filters':
      self.split_ids = self.filtered_ids
      if self.split_ids: #filter_set seems to be initialized
        filt_str = '\n'.join(self.filter_set.get_filters_values())
        self.split_crit_str = 'Filters:\n' + filt_str
      else: 
        self.split_crit_str = post_data.getvalue('split_filter_ta', '')
    # elif self.split_source == 'checkboxes':
      # self.split_ids = sh.get_id_list_from_cb(post_data, 'enzymes')
    elif split_source == 'su_pos_aac': 
      self.set_su_pos_aac_split_ids(post_data) # set su, pos and aac
    else:
      self.split_ids = []
      
  def set_filtered_ids(self, db_cursor):
    query = 'SELECT e.enz_id FROM `enzymes` e INNER JOIN organisms o ' + \
            'ON e.org_id = o.org_id'
    eid_wc = sf.get_where_id_case(self.all_ids, 'enzymes', True)
    f_wc = self.filter_set.get_db_query_filter()
    if eid_wc and f_wc: 
      wc = ' WHERE ' + eid_wc + ' AND ' + f_wc
      enz_id_rows = df.send_query(db_cursor, query + wc)
      for row in enz_id_rows:
        enz_id = sf.try_val_to_int(row['enz_id'])
        if enz_id:
          self.filtered_ids.append(enz_id)
      
  def set_split_filters(self, db_cursor):
    org_id_set = {descr.org_id for descr in self.id_to_descr.values()}
    #make db_obj to get attr cols for making filters:
    db_obj = sc.DbObj()
    attr_rows = df.get_attr_rows(db_cursor)
    # fill attribute columns description list to set organisms and filters:
    db_obj.attr_col_descr_list.fill_from_attr_rows(attr_rows) 
    # make filters to filter rows obtained from database
    self.filter_set = fc.FilterSet(db_cursor, post_data, db_obj, 
                                   self.all_ids, org_id_set)
  def set_from_db(self):
    if self.al_id and self.db_name:
      db_link, db_cursor = df.get_link_and_cursor(self.db_name)
      if db_cursor:
        #set Split at first to get all_ids:
        self.split = sac.Split(db_cursor, self.al_id, self.ref_id)
        if self.split: #if db contains alignment = Split was set successfully:
          self.all_ids = sorted(self.split.all_ids)
          self.id_to_descr = sf.get_enz_id_to_enz_descr(db_cursor, self.all_ids)
          self.set_split_filters(db_cursor)
        if type(self.filter_set).__name__ == 'FilterSet':
          self.set_filtered_ids(db_cursor)
          
  def set_scores_params(self, post_data):
    self.prob_cutoff, self.shen_cutoff, self.rand_samp_num = 0, 0, 0
    self.use_prob = post_data.getvalue('use_prob', False)
    if self.use_prob:
      num_str = post_data.getvalue('prob_cutoff', 0)
      self.prob_cutoff = sf.try_val_to_int(num_str)
    self.use_shen = post_data.getvalue('use_shen', False)
    if self.use_shen:
      num_str = post_data.getvalue('shen_cutoff', 0)
      self.shen_cutoff = sf.try_val_to_int(num_str)
      num_str = post_data.getvalue('rand_samp_num', 40)
      self.rand_samp_num = sf.try_val_to_int(num_str)

  def __init__(self, post_data):
    self.db_name = sh.get_db_name(post_data)
    self.ref_id = sf.try_val_to_int(post_data.getvalue('ref_id', ''))
    self.al_id = sf.try_val_to_int(post_data.getvalue('al_id', ''))
    self.set_scores_params(post_data)
    self.all_filter_str = post_data.getvalue('al_filter_ta', '')
    self.split_crit_str = 'Split criteria isn\'t defined'
    self.filter_set, self.split = None, None
    self.su_pos_aac = []
    self.all_ids, self.split_ids, self.filtered_ids = [], [], []
    self.id_to_descr = dict() #descr is to be converted to str for output
    #fill in split, all_ids, id_to_descr, filter_set and filter_ids:
    self.set_from_db()
    if self.split:
      #get split_ids from one of available sources: filtered enzyme ids, 
      #current split ids or specified aac and set up split_crit_str:
      self.set_split_ids_and_crit(post_data)
      #use split_ids to make split in each split_col in self.split:
      self.split.set_split_cols(self.split_ids, self.use_prob, 
                                self.use_shen, self.rand_samp_num)
      self.split_ids = sorted(self.split_ids)

  def get_id_descr_str(self, id_list):
    return '\n'.join([self.id_to_descr[id].id_name_str for id in id_list])
    
  def get_shen_field(self):
    html = sh.mk_checkbox('use_shen', 'ShEn', self.use_shen) + \
            ', cut-off: <input name = "shen_cutoff" type = "number"' + \
            ' min = "0" value = "' + str(self.shen_cutoff) +'" size = "3"><br>'
    html += ' Rsn: <input title = "Number of random samples to get ShEn ' + \
            'sample" name = "rand_samp_num" type = "number" value = "' + \
            str(self.rand_samp_num) + '" min = "0" size = "6">'
    return html
          
  def get_prob_field(self):
    html = sh.mk_checkbox('use_prob', 'PolProb', self.use_prob)
    html += ', cut-off: <input name = "prob_cutoff" type = "number"' + \
            ' min = "0" value = "' + str(self.prob_cutoff) + '" size = "3">'
    return html
           
  def get_rand_samp_num_field(self):
    return 
           
  def get_filters_panel(self):
    return fh.mk_filter_form(self.filter_set, 'Filters:', main_filters = False,
                             show_col_cb = False)

  def get_split_source_field(self):
    sel_set = {'current_split':'current split ids', 
               'su_pos_aac':'specified aminoacid',
               'filters':'filters'}
    return sh.mk_select('split_source', list(sel_set.keys()), sel_set, 
                       selected_set = sf.to_set('current_split'))
    
  def get_ref_id_field(self):
    width = ' style = "width:200px;"'
    return sh.mk_select('ref_id', self.all_ids, self.id_to_descr, 
                         selected_set = {self.ref_id}, style = width)
                         
  def get_al_filter_str_field_html(self):
    html = 'All alignment filters: <br>'
    html += sh.mk_textarea("al_filter_ta", 4, 10, self.all_filter_str, True)
    return html
    
  def get_split_crit_field_html(self):
    return 'Split criteria:<br>' + sh.mk_textarea("split_crit_ta", 4, 10, 
           self.split_crit_str)
    
  def get_al_enz_id_set_field_html(self):
    html = 'All alignment enzymes: ' + str(len(self.all_ids)) + '<br>'
    html += sh.mk_hidden_field("al_ids", self.all_ids)
    descr = self.get_id_descr_str(self.all_ids)
    html += sh.mk_textarea("al_ids_ta", 4, 40, descr)
    return html
    
  def get_split_enz_id_set_field_html(self):
    html = 'Split enzymes: ' + str(len(self.split_ids)) + '<br>'
    html += sh.mk_hidden_field("split_ids", self.split_ids)
    descr = self.get_id_descr_str(self.split_ids)
    html += sh.mk_textarea("split_ids_ta", 4, 40, descr)
    return html
    
def get_score_color(prob_score, shen_score, cut_off = 30, scale = 1000):
  # scores over cut_off + 1000 (when (score - cut_off)/1000 is over 1) are  
  # painted with britest blue.
  # scores below cut_off aren't painted
  # scores are normalized to get range(0,1) and passed to painter
  # for normal prob*shen scale is 1000 and cut-off is 30
  if prob_score <1:
    prob_score = 1
    scale = 10 #ShEn is about 10-20, so scale should be 10
    cut_off = 3
  else: 
    if shen_score < 3:
      shen_score = 3
  score = prob_score * shen_score
  return hc.GradHtmlColor.get_colors((score - cut_off)/scale)
    
def mk_su_pos_aac_field(su_name, split_col):
    #select_name = (su_name)_(al_pos) to set up su_pos_aac
    select_name = su_name + '_' + str(split_col.ref_aac.al_pos)
    #id = (su_name)(ref_seq_pos) to navigate through cols
    #how to move cell more left? ({inline:"end"} doesn't work)
    id = su_name + str(split_col.ref_aac.seq_pos)
    html = '<input type = "radio" id = "' + id + '" name = "su_pos" ' + \
           'value = "' + select_name + '">'
    html += sh.mk_select(select_name, split_col.aac_names)
    return html
    
def mk_control_panel(s_data):
  html = '<table class = "form_holder">'
  html += '<tr>'
  html += '<td>Set reference enzyme: <br>' + s_data.get_ref_id_field() + '</td>'
  onclick = "showElem(document.getElementById('ref_pos').value)"
  html += '<td><button type = "button" onclick = "' + onclick + \
          '"> Go to pos: </button><br><input id = "ref_pos" size = "8" ' + \
          'type = "text" onchange = "showElem(this.value)"></td>'
  html += '<td>Split source:<br>' + s_data.get_split_source_field() + '</td>'
  html += '<td title = "Leave only cols having score over given value">' + \
          s_data.get_prob_field() + '</td>'
  html += '<td title = "Leave only cols having score over given value">' + \
          s_data.get_shen_field() + '</td>'
  html += '<td>' + sh.mk_submit_btn('Apply', 'splitAn.py') + '</td>'
  html += '</tr>' 
  html += '</table>'
  return html

def mk_info_panel(s_data):
  html = '<div style = "width:100%">'
  html += s_data.get_filters_panel() #filter layer
  html += sh.mk_folded_layer('Settings', mk_control_panel(s_data)) #settings
  info = '<table class = "form_holder"><tr>\n'
  info +=  '<td>' + s_data.get_split_crit_field_html() + '</td>\n'
  info += '<td>' + s_data.get_split_enz_id_set_field_html() + '</td>\n'
  info += '<td>' + s_data.get_al_filter_str_field_html() + '</td>\n'
  info += '<td>' + s_data.get_al_enz_id_set_field_html() + '</td>\n'
  info += '</tr></table>\n'
  html += sh.mk_folded_layer('Info', info)
  html += '</div>\n'
  return html
  
def mk_fract_clr(spl_fract, diff):
  if diff > 20:
    return "#F00"
  if diff > 10:
    return "#F66"
  if diff < -20:
    return "#00F"
  if diff < -10:
    return "#66F"
  if spl_fract > 0:
    return "#CCC"
  return "#666"
  
def mk_fract_ta(split_col):
  html = '<div class = "sum_frame">'
  # for aac in sorted(split_col.all_aac_to_fract.keys()):
  for aac in split_col.aac_order:
    all_fract = round(split_col.all_aac_to_fract[aac]*100, 2)
    spl_fract = round(split_col.spl_aac_to_fract.get(aac, 0)*100, 2)
    diff = round(spl_fract-all_fract, 2)
    f_clr = mk_fract_clr(spl_fract, diff)
    html += '<font color = "' + f_clr + '">' + aac + ': ' + str(all_fract) + \
              ' &rightarrow; ' + str(spl_fract) + ' (' + str(diff) + \
              ')</font><br>\n'
  html += '</div>\n'
  return html
  
def mk_split_table_cell(su_name, split_col, shen_cutoff = 0, prob_cutoff = 0):
  html, sp_c = '', split_col
  # if type(sp_c).__name__ == 'SpacerCol' or \
    # sp_c.shen_score < shen_cutoff or sp_c.prob_score < prob_cutoff:
    # return ''
  bc, fc = get_score_color(sp_c.prob_score, sp_c.shen_score)
  if bc and fc: #score is over color cut-off, painting cell:
    html = '<table style = "background:' + bc + '; color:' + fc + ';">'
  else:
    html = '<table>'
  html += '<tr><td>' + su_name + str(sp_c.ref_aac.al_pos) + ' (' + \
          str(sp_c.ref_aac) + ')</td></tr>'
  html += '<tr><td>' + mk_su_pos_aac_field(su_name, sp_c) + '</td></tr>'
  html += '<tr><td>' + mk_fract_ta(sp_c) + '</td></tr>'
  html += '<tr><td>' + sf.float_to_str(sp_c.all_shen, 2) + ' &rightarrow; ' + \
         sf.float_to_str(sp_c.spl_shen, 2) + ', ' + \
         sf.float_to_str(sp_c.sm, 2) + '&#177;' + \
         sf.float_to_str(sp_c.sd, 2) + '</td></tr>'
  html += '<tr><td>' + sf.float_to_str(sp_c.norm_p_val, 6) + '</td></tr>'
  html += '<tr><td>' + sf.float_to_str(sp_c.shen_score, 2) + '</td></tr>'
  html += '<tr><td>' + sf.float_to_str(sp_c.prob_score, 2) + '</td></tr>'
  html += '</table>\n'
  return html
    
def mk_header_table_cell():
  html = '<table>' 
  html += '<tr><td> subunit[pos] (ref) </td></tr>'
  html += '<tr><td>split by aminoacid </td></tr>'
  html += '''<tr><td><div class = "sum_frame">Aac fractions:<br> 
     all &rightarrow; split (diff)<br> 
     Diff colors: 
     <br><font color = "#F66"> red </font> = over 10%<br>
     <font color = "#F00"> extra red </font> = over 20%<br>
     <font color = "#66F"> blue </font> = below -10% <br> 
     <font color ="#00F"> extra blue </font> = below -20% </div></td></tr>'''
  html += '<tr><td>S<sub>all</sub>&rightarrow;S<sub>split</sub>, ' + \
          'sm &#177; sd </td></tr>'
  html += '<tr><td>S<sub>rand</sub> normality p-val</td></tr>'
  html += '<tr><td>ShEn = |sm - S<sub>split</sub>|/sd</td></tr>'
  html += '<tr><td>PolProb = -lg(P<sub>split</sub>)</td></tr>'
  html += '</table>\n'
  return html
  
def mk_content(split_data):
  sd, split_panel = split_data, hc.Panel(700)
  su_colors = hc.BgFgHtmlColor(sd.split.su_names, contrast_delta = 120)
  names_header, su_header, ct = '', '', '</tr></table> \n'
  names_tbl = '<table class = "viewer"><tr><td>' + mk_header_table_cell() + \
              '</td></tr></table>\n'
  su_tbl = '<table class = "viewer"><tr>'
  for sn, split_cols in sd.split.sn_to_split_cols.items():
    bc, fc = su_colors.get_bg_color(sn), su_colors.get_fg_color(sn)
    for sp_c in split_cols:
      if type(sp_c).__name__ == 'SpacerCol' or \
        sp_c.shen_score < sd.shen_cutoff or sp_c.prob_score < sd.prob_cutoff:
        continue
      su_tbl += '<td style = "background:' + bc + '; color:' + fc + ';">'
      su_tbl += mk_split_table_cell(sn, sp_c, sd.shen_cutoff, sd.prob_cutoff) +\
                '</td>'
  su_tbl += '</tr></table>\n'
  split_panel.add_sect(hc.PanelSect(names_header, names_tbl, 10))
  split_panel.add_sect(hc.PanelSect(su_header, su_tbl, 88))
  return split_panel.get_html()
  
def mk_data_form(s_data, content):# opt_panel, bm_panel, filt_panel):
  on_kd = "return event.key != 'Enter';"
  html = '<form id = "metadata" method = "POST"  onkeydown="' + on_kd + '">'
  html += sh.mk_db_name_field(s_data.db_name)
  html += sh.mk_hidden_field('al_id', str(s_data.al_id))
  html += mk_info_panel(s_data)
  html += content + '</form>\n'
  return html
        
cgitb.enable()
post_data = cgi.FieldStorage()
page_name, status, content, label, html = 'splitAn.py', [], '', '', ''
if not post_data: 
  html = sh.mk_page_header(page_name, no_post_data = True)
else:
  sd = SplitData(post_data) #gather db_name, al_id, filters, etc. from post
  content = mk_content(sd)
  label = ' for database ' + sd.db_name + ', alignment #' + str(sd.al_id)
  #wrap content in data_form with post data for alignment manager:
  content = mk_data_form(sd, content)
  html = sh.mk_page_header(page_name, status, label) + content

print(html)

