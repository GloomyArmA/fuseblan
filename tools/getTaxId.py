import MySQLdb
from contextlib import closing
from sys import argv
import requests

def find_taxid_in_response(response):
  resp_str=str(response.text)
  tax_start=resp_str.find(r'Taxonomy ID:')
  if tax_start>0:
    #looking for '>' which closes <a href...> tag following the 'Taxonomy ID':
    tax_start=resp_str.find('>', tax_start)+1
    #than looking for '<' which opens </a> closing tag:
    tax_end=resp_str.find('<',tax_start)
    tax_id=resp_str[tax_start:tax_end]
    return tax_id
  else:
    print('no "Taxonomy ID" string found')
    return 0

def get_ncbi_taxid(full_name):
  name_parts = full_name.split(' ')
  if len(name_parts) >1:
    name = name_parts[0]+' '+name_parts[1]
    rqst_data = {'name':name,'mode':'LinkOut'}
    rqst_addr = 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi'
    #sending POST request to ncbi and looking for taxid in response:
    return find_taxid_in_response(requests.post(rqst_addr, rqst_data))
    
def add_tax_id(id_name_lines, dest_file):
  for line in id_name_lines:
    name = line[line.find('=') + 1 : line.find('\t')].strip()
    print('request for "' + name + '" ncbi taxid...')
    id = get_ncbi_taxid(name)
    if id:
      print('    got taxid = ', id)
      dest_file.write(line + id + '\n')
  
id_name_lines = []
id_name_file, tax_id_file = argv[1], argv[2]
with closing(open(id_name_file, 'r')) as inf:
  id_name_lines = inf.read().split('\n')
with closing(open(tax_id_file, 'w')) as tif:
  add_tax_id(id_name_lines, tif)
  





