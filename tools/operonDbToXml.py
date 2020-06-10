import xml.dom.minidom as xdm
from contextlib import closing
from copy import deepcopy
from sys import argv

def get_items(sf):
  items = list() #list of items, each item contains all lines of one organism
  item = list() #list of item lines
  for line in sf:
    if line.find(":") > 0:#consider only named (lineName:lineInfo) lines
      if line.startswith("Organism:"): #current item has finished, new started
        if (len(item)):
          items.append(tuple(item))
          item.clear()
      item.append((line.strip("\n").split(':')))
  return items

def mk_su_element(doc, line, operon_name):
  su_el = doc.createElement('subunit')
  su_el.setAttribute('name', line[0])
  su_el.setAttribute('su_operon', operon_name)
  other = line[1].replace(' ','').split(';')
  for attr in other:
    if attr.startswith('Start'):
      su_el.setAttribute('su_start', attr[attr.find('-')+1:])
    if attr.startswith('End'):
      su_el.setAttribute('su_end', attr[attr.find('-')+1:])
    if attr.startswith('Sequ'):
      su_el.setAttribute('su_seq', attr[attr.find('-')+1:])
  return su_el
  
def mk_org_element(doc, org_name, tax_list):
  tax_names = ['tax_sk', 'tax_ph', 'tax_cl', 'tax_or']
  org_el = doc.createElement('organism')
  #TODO: проверка имён организмов!
  org_el.setAttribute('name', org_name)
  for i in range(len(tax_list)):
    org_el.setAttribute(tax_names[i], tax_list[i])
  return org_el

def parse_item(doc, item):
  #item should be a list of line lists from one organism
  org_name, tax_list, enz_attr= '', [], []
  operon_id = 0
  is_reading_su_descr = False
  cur_enz_el, org_el = None, None
  for line in item:
    if line[0].startswith("Organi"):
      org_name = line[1].strip()
      continue
    if line[0].startswith("Taxono"):
      tax_list = line[1].strip().split('\t')
      org_el = mk_org_element(doc, org_name, tax_list)
      continue
    if line[0].startswith("ATP"):
      #subunit description starts from this line
      if cur_enz_el:
        #previous line was the last of previous ATP synthase, writing it out:
        org_el.appendChild(cur_enz_el)
      cur_enz_el = doc.createElement('enzyme')
      #after this all lines will be about synthases, so is_reading_su_descr
      #will always be true )
      #starting new synthase: line[1] contains its unstripped name
      cur_enz_el.setAttribute('name', line[1].replace(' ',''))
      continue
    if line[0].startswith("Operon"): #next subunits belong to new operon
      operon_id += 1
    #if we get here - it could be a subunit line, testing it:
    if line[1].find("Sequence")>1:
      cur_enz_el.appendChild(mk_su_element(doc, line, 'op_' + str(operon_id)))
  #item ends here, but last synthase isn't added because it happens only when reader
  #meets new synthase. Fixing that:
  if cur_enz_el:
    org_el.appendChild(cur_enz_el)
  return org_el
  
def mk_attr_el(doc, attr_vals):
  attr_names = ['table_name', 'col_name', 'label', 'data_type', 'col_group']
  attr_el = doc.createElement('attr')
  for i in range(len(attr_vals)):
    attr_el.setAttribute(attr_names[i], attr_vals[i])
  return attr_el
  
def mk_db_descr_elems(doc, db_el):
  tab_to_attrs = dict()  
  o_attr_cols = [ ["tax_sk", "superkingdom", "ranks", "taxonomy"],
             ["tax_ph", "phylum", "ranks", "taxonomy"],
             ["tax_cl", "class", "ranks", "taxonomy"],
             ["tax_or", "order", "ranks", "taxonomy"] ]
  tab_to_attrs["organisms"] = o_attr_cols
  s_attr_cols = [ ["su_start", "gene start", "ceil_num", "gene placement"],
             ["su_end", "gene end", "ceil_num", "gene placement"],
             ["su_operon", "gene operon", "ranks", "gene placement"]]
  tab_to_attrs["subunits"] = s_attr_cols
  for table_name, attr_cols in tab_to_attrs.items():
    for attr_vals in attr_cols:
      db_el.appendChild(mk_attr_el(doc, [table_name] + attr_vals))
  # return [org_cols_el, enz_cols_el, su_cols_el]

operon_db_file, xml_db_file = argv[1], argv[2]
#operon_db_file, xml_db_file = 'source_operons_short.txt', 'src_db.xml'
doc = xdm.Document()
db = doc.createElement('db')
# db.setAttribute('name', '')
# db.setAttribute('label', '')
doc.appendChild(db)
mk_db_descr_elems(doc, db)
# for el in col_el_list:
  # db.appendChild(el)
with closing(open(operon_db_file, 'r')) as odf:
  items = get_items(odf)
  for item in items:
    db.appendChild(parse_item(doc, item))
  
with closing(open(xml_db_file, 'w')) as xdf:
  xml_str = doc.toprettyxml(indent = '  ')
  xdf.write(xml_str)

