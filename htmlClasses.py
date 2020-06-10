import random #for html su colors
import math
import colorsys

# class PageDescr:
  # def __init__(self, label, form_id, parent_descr = dict()):
    # self.page_name = page_name
    # self.label = label
    # self.form_id = form_id
    # self.parent_names_to_labels = parent_pages
    
  # def get_html(self):
    # html = '<td class = "page_descr">\n'
    # for parent_name, parent_label in parent_pages:
      # html += '<input type = "submit" formaction = "' + parent_name + \
              # '" formmethod = "POST" ' + 'value = "' + parent_label + \
              # '" form = "' + self.form_id + '"> \n'
    # html += '</td><td class = "page_descr">\n' + label + '</td>'
    # return html

class PanelSect:
  # section is a panel part having fixed col_header and horizontally scrolling
  # col_frame. 
  def __init__(self, label, content, width = 0):
    # self.name = name
    self.label = label
    self.width = width
    self.content = content
  
class Panel:
  def __init__(self, content_height_px):
    self.cnt_height_px = str(content_height_px)
    self.sects = []
    self.html = ''
    
  def add_sect(self, panel_sect):
    if not panel_sect.width:
      panel_sect.width = 100/(len(self.sects) + 1)
    self.sects.append(panel_sect)
    total_w = sum([s.width for s in self.sects])
    # print('panel tw:', total_w, '<br>')
    if total_w > 100:
      for sect in self.sects:
        # print('sect_w:',sect.width, ', total_w:',total_w, '<br>')
        sect.width = round(sect.width/total_w, 1)*98
        # print('sect_w:', sect.width, '<br>')

  def _mk_panel(self):
    # open "panel" div and makes "header_frame" with col_headers there
    html = '<div class = "panel">\n  <div class = "header_frame">\n'
    for sect in self.sects:
      html += '    <div class = "col_header" style = "width: ' + \
                   str(sect.width) + '%;">' + sect.label + '</div>\n'
    html += '  </div> \n' #close "header_frame"
    html += '  <div class = "content_frame" style = "height:''' + \
                str(self.cnt_height_px) + 'px;">\n' # open content_frame
    for sect in self.sects:
      html += '    <div class = "col_frame" style = "width: ' + \
               str(sect.width) + '%;">\n'
      # div that holds content and scrolls horizontally inside "col_frame":
      html += '      <div class = "table_holder">\n' + sect.content + '</div>'
      html += '    </div>\n' # close "col_frame" div
    html += '  </div>\n</div>\n' # close "content_frame" and "panel" divs
    self.html = html
    
  def get_html(self):
    if not self.html:
      self._mk_panel()
    return self.html
    
class GradHtmlColor:
  @staticmethod
  def to_hex_str(clr_channel_fraction):
    #converts clr channel fraction [0, 1] to value ['0', 'FF']
    clr_hex = round(clr_channel_fraction * 255, 0)
    clr_hex_str = hex(int(clr_hex))[2:] # get str after '0x'
    if len(clr_hex_str) < 2: #got 'A' from '0xA' instead '0A'
      clr_hex_str = '0'+clr_hex_str
    return clr_hex_str
    
  @staticmethod
  def get_colors(delta):
    #returns bgcolor and text color in str '#rrggbb'. colorsys.hls_to_rgb takes
    #fraction [0, 1] for light and saturation, and returns also fraction [0, 1]
    #for each rgb. So it needs to be coverted in hex
    if delta < 0:
      return '', ''
    pos_hue = 0.6 #blue color for positive delta
    light = 0.5 #display in the middle light range
    satur = delta if delta < 1  else 1
    fg_clr = '#0FF'
    bg = colorsys.hls_to_rgb(pos_hue, light, satur)
    bg = [GradHtmlColor.to_hex_str(clr_fract) for clr_fract in bg]
    bg_clr = '#' + ''.join(bg)
    return bg_clr, fg_clr
    
class BgFgHtmlColor:
  @staticmethod
  def mk_new_color_number(existing_colors, brightness_thresh, match_thresh):
    #color being added to existing_colors shoul not match better than
    #match_thresh with any color in set!
    #colors are in 3 dec coords: r, g and b. 
    new_clr = [random.randint(brightness_thresh,255) for c in[0,1,2]]
    match = False
    for clr in existing_colors:
      #checking metric between two color points:
      distance = math.sqrt(sum((new_clr[i]-clr[i])**2 for i in [0,1,2]))
      if distance < match_thresh:
        match = True
        break
    if match:
      new_clr = BgFgHtmlColor.mk_new_color_number(existing_colors, brightness_thresh, 
                match_thresh)
    return new_clr
  @staticmethod
  def get_contrast(clr, delta):
    #clr is a list of [r, g, b], delta is a difference per channel 
    contrast_clr = []
    for c in clr:
      cc = c-delta if c > delta else c + delta
      contrast_clr.append(cc if cc < 255 else 255)
    return contrast_clr
  @staticmethod
  def rgb_to_html(clr):
    #clr is a list of [r, g, b]
    hex_rgb = []
    for c in clr:
      hc = hex(c)[2:] 
      if len(hc) < 2: #got something less than 0xf
        hc = '0' + hc
      hex_rgb.append(hc)
    return '#'+''.join(hex_rgb)
  
  def mk_html_colors(self, names):
    #makes html bg and fg colors for names. 
    bg_clr_numbers, fg_clr_numbers = dict(), dict()
    for name in names:
      bg_clr_number = self.mk_new_color_number(bg_clr_numbers.values(), 
                      self.brightness_thresh, self.match_thresh)
      bg_clr_numbers[name] = bg_clr_number
      fg_clr_number = self.get_contrast(bg_clr_number, self.contrast_delta)
      #[255-bg_clr_number[i] for i in [0,1,2]]
      fg_clr_numbers[name] = fg_clr_number
    for name in names:
      bg_clr = self.rgb_to_html(bg_clr_numbers[name])
      fg_clr = self.rgb_to_html(fg_clr_numbers[name])
      self.clr_dict[name] = {'bg_color': bg_clr, 'fg_color': fg_clr}

  def __init__(self, names,
               brightness_thresh = 160, 
               match_thresh = 20, 
               contrast_delta = 80):
    self.brightness_thresh = brightness_thresh
    self.match_thresh = match_thresh #min color distance for bg colors
      #if more than 20 - recursion may occur!
    self.contrast_delta = contrast_delta #delta for contrast color
    self.clr_dict = dict()
    self.mk_html_colors(names)
    #print('color dict in BgFgHtmlColor:',self.clr_dict)
    
  def get_bg_color(self, name):
    #print('name is:',name,', color dict names are:',self.clr_dict.keys())
    bgfg = self.clr_dict.get(name, None)
    if bgfg:
      return bgfg.get('bg_color', '#ffffff')    
    return '#ffffff'
    
  def get_fg_color(self, name):
    bgfg = self.clr_dict.get(name, None)
    if bgfg:
      return bgfg.get('fg_color', '#333333')    
    return '#333333'