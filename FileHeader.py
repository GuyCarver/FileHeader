#----------------------------------------------------------------------
# Copyright (c) 2013, Guy Carver
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
#     * The name of Guy Carver may not be used to endorse or promote products # derived#
#       from # this software without specific prior written permission.#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# FILE    FileHeader.py
# BY      Guy Carver
# DATE    06/02/2013 09:13 PM
#----------------------------------------------------------------------

import sublime, sublime_plugin
import os, datetime
from string import Template
import re

sets_file = "FileHeader.sublime-settings"
fh_settings = None

cright_re = re.compile("(.*Copyright \(c\) )[0-9]+(.*)")

def plugin_loaded(  ) :
  global fh_settings
  fh_settings = sublime.load_settings(sets_file)

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
    hr = vw.extract_scope(1)
    lines = vw.lines(hr)
    for lr in lines :
      lt = vw.substr(lr)
      match = cright_re.search(lt)
      if match != None :
        # print("1: {}\r\n".format(match.group(1)))
        # print "2: {}\r\n".format(match.group(2)))
        string = match.group(1) + str(Date()) + match.group(2)
        vw.replace(self.edit, lr, string)
        break

  def HasHeader( self ) :
    #This may be temporary.  Need to use a comment range perhaps?
    vw = self.view
    hr = vw.extract_scope(1)
    lt = vw.substr(hr)
#    print("testing " + lt)
    return (lt.find("Copyright") != -1)

  def run( self, edit, file="FileHeader.txt" ) :
    self.file = file
    self.edit = edit
    #Look for file header.
    if self.HasHeader() :
      # print("Replacing Date")
      self.ReplaceDate()
    else:
      # If it doesn't exist then load header from file, set date/time and add it.
      # print("Adding header")
      self.AddHeader()
