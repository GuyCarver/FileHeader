import sublime, sublime_plugin
import os, datetime
from string import Template
import re

sets_file = "FileHeader.sublime-settings"
fh_settings = sublime.load_settings(sets_file)

cright_re = re.compile("(.*Copyright \(c\) )[0-9]+(.*)")

def UserName(  ) :
  return fh_settings.get("user", "")

def Date(  ) :
  return datetime.date.today().year

def DateTime(  ) :
  t = datetime.datetime.now()
  return(t.strftime("%m/%d/%Y %I:%M %p"))

def HeaderFile( aFile ) :
  filePath = os.path.join(sublime.packages_path(), "User", aFile)
  if not os.access(filePath, os.R_OK) :
    filePath = os.path.join(sublime.packages_path(), "FileHeader", aFile)

  return filePath

class FileHeaderWindowCommand( sublime_plugin.WindowCommand ) :
  """Add file header information to the active view using a Menu Command"""
  def run( self ) :
    vw = self.window.active_view()
    if not vw.is_scratch() :
      vw.run_command("file_header")

class FileHeaderCommand( sublime_plugin.TextCommand ) :
  """Add copyright/info text to beginning of file."""

  def FileName( self ) :
    fn = self.view.name()
    if not fn :
      fn = self.view.file_name()
    if fn :
      fn = os.path.split(fn)[1]
    else:
      fn = "NoFileName"

    return fn

  def Comment( self ) :
    shell_vars = self.view.meta_info("shellVariables", 0)
    c = "//"

    if shell_vars :
      for v in shell_vars :
        if v["name"] == "TM_COMMENT_START" :
          value = v["value"]
          if value :
            c = value.strip()

    return c

  def Do_AddHeader( self ) :
    filePath = HeaderFile(self.file)
    hf = open(filePath)
    if hf :
      contents = hf.read()
      hf.close()
      tp = Template(contents)
      cr = Date()
      c = self.Comment()
      fn = self.FileName()
      u = UserName()
      dt = DateTime()
      contents = tp.safe_substitute(YEAR=cr, FILENAME=fn, USER=u, DATETIME=dt, CC=c)
      self.view.insert(self.edit, 0, contents)

  def GUN_Done( self, aName ) :
    fh_settings.set("user", aName)
    sublime.save_settings(sets_file)
    self.Do_AddHeader()

  def AddHeader( self ) :
    name = UserName()
    if name == "" :
      #GUN_Done will run self.Do_AddHeader().  We are going to continue execution
      #NOTE: self.edit will end before GUN_Done is called.
      self.view.window().show_input_panel("Enter user name:", name, self.GUN_Done, None, None)
    else:
      self.Do_AddHeader()

  def ReplaceDate( self ) :
    vw = self.view
    #May want to change this range to be more flexible.
    for i in range(2, 16) :
      lp = vw.text_point(i, 0)
      lr = vw.line(lp)
      lt = vw.substr(lr)
      match = cright_re.search(lt)
      if match != None :
        # print "1: %s\r\n" % match.group(1)
        # print "2: %s\r\n" % match.group(2)
        string = match.group(1) + "2012" + match.group(2)
        vw.replace(self.edit, lr, string)
        break

  def HasHeader( self ) :
    #This may be temporary.  Need to use a comment range perhaps?
    vw = self.view
    lp0 = vw.text_point(0, 0)
    lp1 = vw.text_point(21, 0)
    lr0 = vw.line(lp0)
    lr1 = vw.line(lp1)
    hr = sublime.Region(lr0.a, lr1.b)
    lt = vw.substr(hr)
#    print "testing" + lt
    return (lt.find("Copyright") != -1)

  def run( self, edit, file="FileHeader.txt" ) :
    self.file = file
    self.edit = self.view.begin_edit('FileHeader')
    try:
      #Look for file header.
      if self.HasHeader() :
        # print "Replacing Date"
        self.ReplaceDate()
      else:
        # If it doesn't exist then load header from file, set date/time and add it.
        # print "Adding header"
        self.AddHeader()
    finally:
      self.view.end_edit(self.edit)
