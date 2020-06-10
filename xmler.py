import xml.dom.minidom
import dbFace as df
import sharedFuncs as sf
import sharedClasses as sc
from contextlib import closing

#<db>
#  <attr table_name = 'subunits' col_name = 'su_start' 
#        label = 'sububit gene start' data_type = 'ceil_num' col_group = 'main'>
#  <attr table_name = ....
#  <organism name = "Acaryochloris marina MBIC11017" ...>
#    <enzyme name = "F" ...>
#      <subunit name = "alpha" su_seq = "MKNK..." .../>
#      <sububit name = "beta" su_seq = "...  />
#    </enzyme>
#    <enzyme name = "F" ...>
#      <subunit name = "alpha" su_seq = "... />
#      ...
#    </enzyme>
#  </organism>
#</db>

# col_obj_attrs = ['table_name', 'col_name', 'label', 'data_type', 'col_group']

def mk_attr_dict(elem):
  attr_dict = dict()
  ea = elem.attributes
  for key in ea.keys():
    attr_dict[key] = ea[key].value
  return attr_dict

def mk_attr_col_descr_from_elem(elem):
  # ea = elem.attributes
  # print('ea:', ea.keys())
  # print('ea.table_name:', ea['table_name'].value)
  ea = mk_attr_dict(elem)
  if set(sc.AttrColDescr.vars) <= set(ea.keys()):
    return sc.AttrColDescr(ea['table_name'], ea['col_name'], ea['label'], 
                   ea['data_type'], ea['col_group'])
  return None
 
def mk_obj_from_elem(elem):
  obj_id = 0
  obj_name = elem.getAttribute('name')
  if obj_name:
    if elem.tagName == 'subunit':
      su_seq = elem.getAttribute('su_seq')
      if su_seq:
        return sc.Subunit(obj_id, obj_name, su_seq)
      return '<subunit> lacks name or sequence attribute'
    if elem.tagName == 'enzyme':
      return sc.Enzyme(obj_id, obj_name)
    if elem.tagName == 'organism':
      return sc.Organism(obj_id, obj_name)
  return '<'+ elem.tagName + '> lacks "name" attribute'
    
def fill_attr_descr_from_elem(obj, attr_col_names, elem):
  try:
    obj.fill_attr(attr_col_names, mk_attr_dict(elem))
  except Exception as e:
    return str(e)
  return ''
    
def mk_objs_from_elems(table_name, attr_col_descr_list, elems, err_list):
  col_names = attr_col_descr_list.get_table_col_names(table_name)
  obj, objs = None, []
  for el in elems:
    obj = mk_obj_from_elem(el)
    if type(obj).__name__ == 'str': # error string's been returned
      err_list.append(obj)
      continue
    if type(obj).__name__ == 'Enzyme': 
      su_list = mk_objs_from_elems('subunits', attr_col_descr_list,
                                   el.getElementsByTagName('subunit'), err_list)
      obj.add_subunits(su_list)
    if type(obj).__name__ == 'Organism':
      enz_list = mk_objs_from_elems('enzymes', attr_col_descr_list,
                                    el.getElementsByTagName('enzyme'), err_list)
      obj.add_enzymes(enz_list)
    fill_attr_descr_from_elem(obj, col_names, el)
    objs.append(obj)
  return objs
  
def get_xml_doc_el(xml_content):
  try:
    dom = xml.dom.minidom.parseString(xml_content)
    dom.normalize()
    doc_el = dom.documentElement #root xml element <db>
  except Exception as e:
    return ['An error occured while parsing an xml file:' +str(e)]
  return doc_el

def get_db_obj_from_xml(src_xml_content):
  #look for root tag 'db_col_descr', make AttrColDescr list of them,
  #then look for all 'organism' tags, go through all the attributes
  #with the names mentioned in AttrColDescr for table 'organism'.
  #In 'organism' branch find all 'enzyme' tags, and get the attributes
  #with the names mentioned in AttrColDescr for table 'enzymes'. 
  #Do the same for all 'subunit' tags in 'enzyme' branch. 
  #Return str if error, otherwise 
  db_el = get_xml_doc_el(src_xml_content)
  if type(db_el).__name__ == 'list':
    return ['Failed to create root xml element, check xml file.'] + db_el
  attr_elems = db_el.getElementsByTagName('attr')
  if not attr_elems:
    return ['No <attr> found in xml']
  db_obj = sc.DbObj()
  for a_el in attr_elems: # fill DbObj with attributes col descriptions
    db_obj.attr_col_descr_list.add_col(mk_attr_col_descr_from_elem(a_el))
  org_elems = db_el.getElementsByTagName('organism')
  if not org_elems:
    return ['No <organism> elements found in xml']
  err_list = []
  org_list = mk_objs_from_elems('organisms', db_obj.attr_col_descr_list, 
                                                    org_elems, err_list)
  if err_list:
    return err_list
  db_obj.org_list_obj.set_org_list(org_list)
  return db_obj
  
def mk_elem_from_attr_col_descr(attr_col_descr, doc):
  a_el = doc.createElement('attr')
  for item in sc.AttrColDescr.vars:
    a_el.setAttribute(item, eval('attr_col_descr.'+item))
  return a_el
  
def fill_attrs_in_elem(data_obj, elem):
  for key, val in data_obj.attr_to_val.items():
    elem.setAttribute(key, sf.to_str(val))

def mk_data_obj_elem(data_obj, tag, doc):
  do_el = doc.createElement(tag)
  # print('data object name:',data_obj.name, ', type: ', type(data_obj).__name__, '<br>')
  do_el.setAttribute('name', data_obj.name)
  if tag == 'subunit':
    do_el.setAttribute('su_seq', data_obj.su_seq)
  fill_attrs_in_elem(data_obj, do_el)
  return do_el
    
def mk_elem_from_org(org, doc):
  try:
    o_el = mk_data_obj_elem(org, 'organism', doc)
    for enz in org.enz_id_to_enz.values():
      e_el = mk_data_obj_elem(enz, 'enzyme', doc)
      for su in enz.su_id_to_su.values():
        s_el = mk_data_obj_elem(su,'subunit', doc)
        e_el.appendChild(s_el)
      o_el.appendChild(e_el)
    return o_el
  except Exception as e:
    return doc.createElement('org_error' + str(e).replace(' ','_'))
  
def mk_xml_from_db_obj(db_obj, dest_xml):
  doc = xml.dom.minidom.Document()
  db = doc.createElement('db')
  doc.appendChild(db)
  # print('db_obj org attrs for xmler:', db_obj.attr_col_descr_list.get_table_col_names('organisms'), '<br>')
  for attr_col_descr in db_obj.attr_col_descr_list.all_cols:
    if type(attr_col_descr).__name__ == 'AttrColDescr':
      db.appendChild(mk_elem_from_attr_col_descr(attr_col_descr, doc))
  for org in db_obj.get_org_list():
    if type(org).__name__ == 'Organism':
      db.appendChild(mk_elem_from_org(org, doc))
  xml_str = doc.toprettyxml()
  with closing(dest_xml) as dx:
    dx.write(xml_str)
    
# def get_page_level(parents_list, cur_el, page_name):
  # parents_list.append(cur_el.getAttribute('name')
  # for child in cur_el.childNodes:
    # cur_pn = child.getAttribute('name')
    # if cur_pn == page_name:
      # return parents_list
    # else:
      # cur_get_page_level(parents_list, child, page_name)
    
# def get_page_level(page_name):
  # with closing(open('page_level_cfg.xml', 'r')) as cfg:
    # xml_content = cfg.read()
    # doc_el = get_xml_doc_el(xml_content)
    # if type(doc_el).__name__ != 'list':
      # cur_name = ''
      # for  
  
    
    
# f = open('src.xml', 'r')
# org_list = get_org_list_from_xml(f.read())
# # for org in org_list.org_list:
  # # print('org name:', org.name)
# for attr in org_list.attr_col_descr_list.all_cols:
  # print('attr:', attr.__dict__)

    
  