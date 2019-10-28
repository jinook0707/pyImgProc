# coding: UTF-8

"""
pyImgProc
An open-source software written in Python 
  for processing a batch of images. 

This program was coded and tested in macOS 10.13.

Jinook Oh, Cognitive Biology department, University of Vienna
October 2019.

Dependency:
    wxPython (4.0)
    NumPy (1.15)
    Pillow (6.1)

------------------------------------------------------------------------
Copyright (C) 2019 Jinook Oh, W. Tecumseh Fitch 
- Contact: jinook.oh@univie.ac.at, tecumseh.fitch@univie.ac.at

This program is free software: you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the 
Free Software Foundation, either version 3 of the License, or (at your 
option) any later version.

This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License along 
with this program.  If not, see <http://www.gnu.org/licenses/>.
------------------------------------------------------------------------


Changelog
------------------------------------------------------------------------
v.0.1: (2019.Oct.)
  - Initial development.
v.0.1.1: (2019.Oct.22.)
  - Adding more functions, flip, masking, type... 
"""

import sys
from os import path, getcwd, mkdir
from copy import copy
from glob import glob

import wx, wx.adv
import wx.lib.scrolledpanel as SPanel 
import wx.lib.agw.multidirdialog as MDD
import numpy as np
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

from fFuncNClasses import get_time_stamp, GNU_notice, writeFile, getWXFonts
from fFuncNClasses import setupStaticText, updateFrameSize, str2num

DEBUG = False 
CWD = getcwd()
__version__ = "0.1.1"


#=======================================================================

class ImgProcsFrame(wx.Frame):
    """ Frame for ImgProcs 

    Attributes:
        Each attribute is commented in 'setting up attributes' section.
    """

    def __init__(self):
        if DEBUG: print("ImgProcsFrame.__init__()")

        ### init frame
        w_pos = [0, 25]
        wg = wx.Display(0).GetGeometry()
        wSz = (wg[2], int(wg[3]*0.9))
        wx.Frame.__init__(
              self, 
              None, 
              -1, 
              "pyImgProc v.%s"%(__version__), 
              pos = tuple(w_pos), 
              size = tuple(wSz),
              style=wx.DEFAULT_FRAME_STYLE^(wx.RESIZE_BORDER|wx.MAXIMIZE_BOX),
                         ) 
        self.SetBackgroundColour('#333333')

        ### set app icon 
        self.tbIcon = wx.adv.TaskBarIcon(iconType=wx.adv.TBI_DOCK)
        icon = wx.Icon("icon.ico")
        self.tbIcon.SetIcon(icon)

        ##### beginning of setting up attributes ----- 
        self.w_pos = w_pos # window position
        self.wSz = wSz # window size
        self.fonts = getWXFonts(initFontSz=8, numFonts=3)
        pi = self.setPanelInfo()
        self.pi = pi # pnael information
        self.gbs = {} # for GridBagSizer
        self.panel = {} # panels
        self.timer = {} # timers
        self.selectedFolders = [] # list of selected folders
        self.fileList = [] # file list of images to process 
        self.imgProcOptions = [
                                'crop',
                                'crop_ratio',
                                'masking',
                                'resize',
                                'resize_ratio',
                                'rotate',
                                'flip',
                                'brighten',
                                'darken',
                                'text',
                              ] # image processing options 
        self.ipParams = dict(
                                crop = ['x', 'y', 'w', 'h'],
                                crop_ratio = ['x', 'y', 'w', 'h'],
                                masking = ['fill-color'],
                                resize = ['w', 'h'],
                                resize_ratio = ['w', 'h'],
                                rotate = ['deg', 'expand'],
                                flip = ['direction'],
                                brighten = ['value'],
                                darken = ['value'],
                                text = ['text', 'x', 'y', 'font-size', 'color'],
                             ) # parameters for each image processing
        self.ipParamDesc = dict(
            crop = [
                'x-coordinate to start (pixel)',
                'y-coordinate to start (pixel)',
                'width of cropped image (pixel)',
                'height of cropped image (pixel)'
                ],
            crop_ratio = [
                'x-coordinate to start (0.0-1.0)',
                'y-coordinate to start (0.0-1.0)',
                'width of cropped image (0.0-1.0)',
                'height of cropped image (0.0-1.0)'
                ],
            masking = [
                'color to fill where black in masking image (hexadecimal)',
                ],
            resize = [
                'width of image (pixel)',
                'height of image (pixel)'
                ],
            resize_ratio = [
                'width in float (1.0 = original size)',
                'height in float (1.0 = original size)',
                ],
            rotate = [
                'degree to rotate (0-360)',
                'expand to contain rotated image (0 or 1)',
                ],
            flip = [
                'direction (0-2; 0:horizontal, 1:vertical, 2:both)',
                ],
            brighten = [
                'pixel value to add'
                ],
            darken = [
                'pixel value to subtract'
                ],
            text = [
                'text to insert',
                'x-coordinate (0.0-1.0)',
                'y-coordinate (0.0-1.0)',
                'font size (integer)',
                'font color (hexadecimal)',
                ],
        ) # description of parameters
        self.ipParamVal = dict(
                                crop = [0, 0, 1, 1],
                                crop_ratio = [0.0, 0.0, 0.5, 0.5],
                                masking = ['#000000'], 
                                resize = [1, 1],
                                resize_ratio = [0.1, 0.1],
                                rotate = [0, 0],
                                flip = [0],
                                brighten = [20],
                                darken = [20],
                                text = ['', 0.0, 0.0, 12, '#000000'],
                              ) # default value of each parameter
        # max. number of parameters among all processes
        self.mNumParam = -1 
        for k in self.ipParams.keys():
            n = len(self.ipParams[k])
            if self.mNumParam < n: self.mNumParam = copy(n)
        self.iImgArr = None # numpy array of input image
        self.oImgArr = None # numpy array of output image
        self.logFile = "log_pyImgProc.txt"
        # extension list to recognize as an image file for processing
        self.extList = ['bmp', 'png', 'jpg', 'gif', 'pcx', 'tif', 'tiff'] 
        self.procList = [] # image processing list to execute
        self.maskFP = "mask.png" # masking image
        ##### end of setting up attributes -----  
        
        ### make log file 
        logHeader = "Timestamp, Image file name, Processes\n"
        logHeader += "# ----------------------------------------\n"
        if not path.isfile(self.logFile): # log file doesn't exist
            writeFile(self.logFile, logHeader) # write header

        ### create panels
        for pk in pi.keys():
            self.panel[pk] = SPanel.ScrolledPanel(
                                                  self, 
                                                  name="%s_panel"%(pk), 
                                                  pos=pi[pk]["pos"], 
                                                  size=pi[pk]["sz"], 
                                                  style=pi[pk]["style"],
                                                 )
            self.panel[pk].SetBackgroundColour(pi[pk]["bgCol"]) 
            #if pk in ["ip", "op"]:
            #    self.panel[pk].Bind(wx.EVT_PAINT, self.onPaint)

        def add2gbs(gbs,
                    widget,
                    pos,
                    span=(1,1),
                    bw=5,
                    flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL):
            gbs.Add(widget, pos=pos, span=span, flag=flag, border=bw) 
        ##### beginning of setting up UI panel interface -----
        bw = 5 # border width for GridBagSizer
        nCol = 4 # number columns
        hlSz = (pi["ui"]["sz"][0]-50, -1) # size of horizontal line separator
        vlSz = (-1, 20) # size of vertical line seprator
        self.gbs["ui"] = wx.GridBagSizer(0,0)
        row = 0
        col = 0
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Select folders",
                            name="selFolders_btn",
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        col += 1
        chk = wx.CheckBox(
                            self.panel["ui"],
                            -1,
                            label="Include sub-folders",
                            name="subFolders_chk",
                         )
        chk.SetValue(False)
        add2gbs(self.gbs["ui"], chk, (row,col), (1,1))
        row += 1; col = 0
        sTxt = setupStaticText(
                            self.panel["ui"], 
                            "Selected folders", 
                            font=self.fonts[2],
                              )
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        row += 1; col = 0
        txt = wx.TextCtrl(
                            self.panel["ui"], 
                            -1, 
                            value="[EMPTY]; Please select folders",
                            name="selDir_txt",
                            size=(hlSz[0], 75),
                            style=wx.TE_MULTILINE|wx.TE_READONLY,
                         )
        txt.SetBackgroundColour('#999999')
        add2gbs(self.gbs["ui"], txt, (row,col), (1,nCol))
        row += 1; col = 0
        add2gbs(self.gbs["ui"], 
                wx.StaticLine(self.panel["ui"],
                              -1,
                              size=hlSz,
                              style=wx.LI_HORIZONTAL),
                (row,col), 
                (1,nCol)) # horizontal line separator
        row += 1; col = 0
        lbl = "Target files (you can use wildcard characters)"
        sTxt = setupStaticText(
                            self.panel["ui"], 
                            lbl, 
                            font=self.fonts[2],
                              )
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        row += 1; col = 0
        lbl = "Allowed extensions: %s"%(str(self.extList))
        sTxt = setupStaticText(
                            self.panel["ui"], 
                            lbl, 
                            font=self.fonts[1],
                              )
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        row += 1; col = 0
        txt = wx.TextCtrl(
                            self.panel["ui"], 
                            -1, 
                            value="*.*",
                            name="targetFN_txt",
                            size=(hlSz[0], -1),
                            style=wx.TE_PROCESS_ENTER,
                         )
        txt.Bind(wx.EVT_TEXT_ENTER, self.onEnteredInTC)
        add2gbs(self.gbs["ui"], txt, (row,col), (1,nCol))
        row += 1; col = 0
        add2gbs(self.gbs["ui"], 
                wx.StaticLine(self.panel["ui"],
                              -1,
                              size=hlSz,
                              style=wx.LI_HORIZONTAL),
                (row,col), 
                (1,nCol)) # horizontal line separator
        row += 1; col = 0
        sTxt = setupStaticText(
                            self.panel["ui"], 
                            "List of files to be processed", 
                            font=self.fonts[2],
                              )
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        row += 1; col = 0
        lstCtrl = wx.ListCtrl(
                            self.panel["ui"],
                            -1,
                            name="selFile_lst",
                            size=(hlSz[0], 100),
                            style=wx.LC_REPORT|wx.LC_SINGLE_SEL,
                             ) # selected files to be processed 
        lstCtrl.AppendColumn("FilePath")
        lstCtrl.SetColumnWidth(0, lstCtrl.GetSize()[0])
        lstCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelectedInLC)
        add2gbs(self.gbs["ui"], lstCtrl, (row,col), (1,nCol))
        row += 1; col = 0
        add2gbs(self.gbs["ui"], 
                wx.StaticLine(self.panel["ui"],
                              -1,
                              size=hlSz,
                              style=wx.LI_HORIZONTAL),
                (row,col), 
                (1,nCol)) # horizontal line separator
        row += 1; col = 0
        sTxt = setupStaticText(
                            self.panel["ui"], 
                            "Processes to apply on each image", 
                            font=self.fonts[2],
                              )
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        row += 1; col = 0
        cho = wx.Choice(
                            self.panel["ui"], 
                            -1,
                            name="imgProcOption_cho",
                            choices=self.imgProcOptions,
                       )
        cho.Bind(wx.EVT_CHOICE, self.onChoice)
        add2gbs(self.gbs["ui"], cho, (row,col), (1,1))
        row += 1; col = 0
        lstCtrl = wx.ListCtrl(
                            self.panel["ui"],
                            -1,
                            name="proc_lst",
                            size=(hlSz[0], 100),
                            style=wx.LC_REPORT|wx.LC_SINGLE_SEL,
                             ) # processes to apply on each image  
        colW = lstCtrl.GetSize()[0]/(self.mNumParam+1) # set column width
        lstCtrl.AppendColumn("Process")
        for i in range(self.mNumParam):
            # add column name for parameter
            lstCtrl.AppendColumn("Param%i"%(i)) 
            lstCtrl.SetColumnWidth(i, colW)
        lstCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelectedInLC)
        add2gbs(self.gbs["ui"], lstCtrl, (row,col), (1,nCol)) 
        row += 1; col = 0
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Clear selected",
                            name="clearProc_btn",
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        col += 1
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Clear all",
                            name="clearAllProc_btn",
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        col += 1
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Move Up",
                            name="moveProcUp_btn",
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        col += 1
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Move Down",
                            name="moveProcDown_btn",
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        row += 1; col = 0
        sTxt = setupStaticText(self.panel["ui"], " ", font=self.fonts[1])
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,1))
        col += 1
        sTxt = setupStaticText(
                                self.panel["ui"], 
                                "", 
                                name="processName_sTxt",
                                font=self.fonts[1])
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,1))
        for i in range(self.mNumParam):
            row += 1; col = 0
            sTxt = setupStaticText(self.panel["ui"], 
                                   "", 
                                   name="param%i_sTxt"%(i),
                                   font=self.fonts[1])
            add2gbs(self.gbs["ui"], sTxt, (row,col), (1,3))
            sTxt.Hide()
            col += 3 
            txt = wx.TextCtrl(self.panel["ui"], 
                              -1, 
                              value="",
                              name="param%i_txt"%(i),
                              size=(100, -1))
            add2gbs(self.gbs["ui"], txt, (row,col), (1,1))
            txt.Hide()
        row += 1; col = 0
        
        col += 3
        btn = wx.Button(self.panel["ui"],
                        -1,
                        label="Update",
                        name="updateParam_btn")
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,1))
        btn.Hide()
        row += 1; col = 0
        btn = wx.Button(
                            self.panel["ui"],
                            -1,
                            label="Process all files",
                            name="run_btn",
                            size=(hlSz[0],-1),
                       )
        btn.Bind(wx.EVT_LEFT_DOWN, self.onButtonPressDown)
        add2gbs(self.gbs["ui"], btn, (row,col), (1,nCol))
        row += 1; col = 0
        sTxt = setupStaticText(self.panel["ui"], " ", font=self.fonts[1])
        add2gbs(self.gbs["ui"], sTxt, (row,col), (1,nCol))
        self.panel["ui"].SetSizer(self.gbs["ui"])
        self.gbs["ui"].Layout()
        self.panel["ui"].SetupScrolling()
        ##### end of setting up UI panel interface -----
        
        ##### beginning of setting up input image panel -----
        self.gbs["ip"] = wx.GridBagSizer(0,0)
        row = 0
        col = 0
        sBmp = wx.StaticBitmap(self.panel["ip"], name="ip_sBmp")
        add2gbs(self.gbs["ip"], sBmp, (row,col), (1,1))
        self.panel["ip"].SetSizer(self.gbs["ip"])
        self.gbs["ip"].Layout()
        self.panel["ip"].SetupScrolling()
        ##### end of setting up input image panel -----

        ##### beginning of setting up outpu image panel -----
        self.gbs["op"] = wx.GridBagSizer(0,0)
        row = 0
        col = 0
        sBmp = wx.StaticBitmap(self.panel["op"], name="op_sBmp")
        add2gbs(self.gbs["op"], sBmp, (row,col), (1,1))
        self.panel["op"].SetSizer(self.gbs["op"])
        self.gbs["op"].Layout()
        self.panel["op"].SetupScrolling()
        ##### end of setting up output image panel -----

        ### set up menu
        menuBar = wx.MenuBar()
        fileRenMenu = wx.Menu()
        selectFolders = fileRenMenu.Append(
                            wx.Window.NewControlId(), 
                            item="Select folders\tCTRL+O",
                                        )
        self.Bind(wx.EVT_MENU,
                  lambda event: self.onButtonPressDown(event, 'selectFolders'),
                  selectFolders)
        quit = fileRenMenu.Append(
                            wx.Window.NewControlId(), 
                            item="Quit\tCTRL+Q",
                                 )
        menuBar.Append(fileRenMenu, "&ImageProcessor")
        self.SetMenuBar(menuBar)
        
        ### set up hot keys
        idSelFolders = wx.Window.NewControlId()
        idQuit = wx.Window.NewControlId()
        self.Bind(wx.EVT_MENU,
                  lambda event: self.onButtonPressDown(event, 'selectFolders'),
                  id=idSelFolders)
        self.Bind(wx.EVT_MENU, self.onClose, id=idQuit)
        accel_tbl = wx.AcceleratorTable([ 
                                    (wx.ACCEL_CMD,  ord('O'), idSelFolders), 
                                    (wx.ACCEL_CMD,  ord('Q'), idQuit), 
                                        ]) 
        self.SetAcceleratorTable(accel_tbl)

        ### set up status-bar
        self.statusbar = self.CreateStatusBar(1)
        self.sbBgCol = self.statusbar.GetBackgroundColour()
        self.timer["sbTimer"] = None 

        updateFrameSize(self, wSz)

        self.Bind(wx.EVT_CLOSE, self.onClose)

    #-------------------------------------------------------------------

    def setPanelInfo(self):
        """ Set up panel information.

        Args: 
            None

        Returns:
            pi (dict): Panel information.
        """
        if DEBUG: print("ImgProcsFrame.setPanelInfo()")

        wSz = self.GetSize() # window size
        
        pi = {} # panel information 
        # top panel for UI 
        pi["ui"] = dict(pos=(0, 0), 
                         sz=(int(wSz[0]*0.4), wSz[1]), 
                         bgCol="#cccccc", 
                         style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        uiSz = pi["ui"]["sz"]
        # panel for showing input image
        pi["ip"] = dict(pos=(uiSz[0], 0),
                        sz=(wSz[0]-uiSz[0], wSz[1]/2),
                        bgCol="#999999",
                        style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        ipSz = pi["ip"]["sz"]
        # panel for showing output image 
        pi["op"] = dict(pos=(uiSz[0], ipSz[1]),
                        sz=(wSz[0]-uiSz[0], wSz[1]/2),
                        bgCol="#333333",
                        style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        return pi 

    #-------------------------------------------------------------------
   
    def onButtonPressDown(self, event, flag=''):
        """ wx.Butotn was pressed.

        Args:
            event (wx.Event)
            flag (str, optional): Specifying intended operation of 
              the function call.

        Returns: 
            None
        """
        if DEBUG: print("ImgProcsFrame.onButtonPressDown()")

        objName = ''
        if flag == '':
            obj = event.GetEventObject()
            objName = obj.GetName()

        if flag == "selectFolders" or objName == "selFolders_btn":
            self.selectFolders() 

        elif objName == "run_btn":
            self.showHideProcParamWidgets() # hide all parameter widgets
            self.runImgProc() 

        elif objName == "clearProc_btn":
            self.showHideProcParamWidgets() # hide all parameter widgets
            lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
            idx = lc.GetFirstSelected()
            itemTxt = lc.GetItemText(idx) 
            lc.DeleteItem(idx) # delete selected item
            self.procList.remove(itemTxt) # remove from planned processing list

        elif objName == "clearAllProc_btn":
            self.showHideProcParamWidgets() # hide all parameter widgets
            ### remove all planned processes 
            lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
            lc.DeleteAllItems() # delete all items
            self.procList = [] # delete all planned processing list

        elif objName == "moveProcUp_btn":
            lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
            self.moveItemInLC(lc, 'up') 
        
        elif objName == "moveProcDown_btn":
            lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
            self.moveItemInLC(lc, 'down') 

        elif objName == "updateParam_btn":
            self.updateParamValues() # update parameters
            self.showHideProcParamWidgets() # hide all parameter widgets
   
    #-------------------------------------------------------------------
    
    def moveItemInLC(self, lc, flag):
        """ Move an item (row) upward/downward in wx.ListCtrl

        Args:
            lc (wx.ListCtrl)
            flag (str): up or down

        Returns:
            None
        """
        ri = lc.GetFirstSelected() 
        ### set new row index
        if flag == 'up': newRI = ri - 1
        elif flag == 'down': newRI = ri + 2 
        # return if it's unnecessary to move item
        if (flag == 'up' and newRI < 0) or \
          (flag == 'down' and newRI > lc.GetItemCount()): return
        ### move item
        for ci in range(self.mNumParam+1):
            item = lc.GetItem(ri, ci) # column item
            if ci == 0: # 1st column
                item.SetId(newRI) # set row index
                lc.InsertItem(item) # insert the 1st column item
                # increase row index by one, 
                #   if a new item got just inserted above
                if flag == 'up': ri += 1 
            else:
                # get the column index and copy it to the new row
                lc.SetItem(newRI, ci, item.GetText()) 
        # deselect the previous row
        lc.SetItemState(ri, 0, wx.LIST_STATE_SELECTED) 
        # select newly inserted row 
        lc.SetItemState(newRI, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED) 
        # delete the previous row 
        lc.DeleteItem(ri)
    
    #-------------------------------------------------------------------
    
    def selectFolders(self):
        """ Select folders 

        Args: None

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.selectFolders()")
        
        dlg = MDD.MultiDirDialog(
                     None, 
                     title="Select folders with images to process.",
                     defaultPath=CWD,
                     agwStyle=MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST,
                                ) # select multiple folders
        if dlg.ShowModal() == wx.ID_OK:
            self.selectedFolders = dlg.GetPaths()
            if sys.platform == 'darwin': # OS X
                ### remove root string
                for i, fp in enumerate(self.selectedFolders):
                    si = fp.find("/")
                    if si != -1:
                        fp = fp[fp.index("/"):] # cut off the fisrt directory name,
                          # MultiDirDialog returns with disk name as root
                          # Instead of '/tmp', 
                          # it returns 'Macintosh HD/tmp'.
                    self.selectedFolders[i] = fp 

            ### include sub folder, 
            ###   if "including sub folder" option was checked.
            sfChk = wx.FindWindowByName("subFolders_chk", self.panel["ui"])
            if sfChk.GetValue() == True:
                ### update folder lists
                folderL = copy(self.selectedFolders)
                self.selectedFolders = []
                for dp in folderL:
                # go through selected folders
                    self.selectedFolders.append(dp) # append the selected folder
                    self.addFolders(dp) # add sub-folders in this folder

            ### show folder list in UI
            selDir_txt = wx.FindWindowByName("selDir_txt", 
                                             self.panel["ui"])
            _txt = str(self.selectedFolders)
            _txt = _txt.strip("[]").replace("'","").replace(", ","\n\n")
            selDir_txt.SetValue(_txt) # show list of selected folders

            self.updateFileList() # update files to be renamed
        dlg.Destroy()

    #-------------------------------------------------------------------
    
    def updateParamValues(self):
        """ Update parameter values for an image processing

        Args: None

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.updateParamValues()")
        
        w = wx.FindWindowByName("processName_sTxt", self.panel["ui"])
        pn = w.GetLabel() # process name
        nP = len(self.ipParams[pn]) # number of parameters
        lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
        ### set row index
        rowIdx = -1
        for i in range(lc.GetItemCount()):
            iTxt = lc.GetItemText(i)
            if iTxt == pn: rowIdx = i
        if rowIdx == -1: return
        ### update
        for i in range(nP):
            w = wx.FindWindowByName("param%i_txt"%(i), 
                                    self.panel["ui"])
            txt = w.GetValue().strip()
            currV = self.ipParamVal[pn][i]
            if type(currV) == str:
            # current value is string 
                if len(currV) > 0 and currV[0] == '#':
                # hexadecimal color code
                    if txt[0] != '#': txt = '#' + txt 
                val = txt
            else:
            # in other cases, convert text to number 
                val = str2num(txt)
                if val == None:
                    msg = "%s is not a number." %(txt)
                    wx.MessageBox(msg, 'Error', wx.OK|wx.ICON_ERROR)
                    continue
            self.ipParamVal[pn][i] = val # update param. value
            # show the value in UI 
            lc.SetItem(rowIdx, i+1, "%s: %s"%(self.ipParams[pn][i], str(val))) 
    
    #-------------------------------------------------------------------

    def onChoice(self, event):
        """ wx.Choice was changed.

        Args: event (wx.Event)

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.onChoice()")
        
        obj = event.GetEventObject()
        objName = obj.GetName()
        objVal = obj.GetString(obj.GetSelection()) # text of chosen option

        ### update newFN_txt with option choice.
        if objName == 'imgProcOption_cho':
            if objVal == '': return
            ### update ListCtrl to show files to be processed 
            lc = wx.FindWindowByName("proc_lst", self.panel["ui"])
            lst = [lc.GetItemText(x) for x in range(lc.GetItemCount())]
            pn = objVal
            if pn not in lst:
            # if the chosen process is not already in the list
                rowVal = [pn]
                self.procList.append(pn) # store process name
                for i in range(len(self.ipParams[pn])):
                    _str = "%s:"%(self.ipParams[pn][i])
                    _str += " %s"%(self.ipParamVal[pn][i])
                    rowVal.append(_str)
                lc.Append(rowVal) # show it in the listCtrl
    
    #-------------------------------------------------------------------
    
    def onItemSelectedInLC(self, event):
        """ An item was selected in wx.ListCtrl 

        Args: event (wx.Event)

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.onItemSelectedInLC()")

        obj = event.GetEventObject()
        objName = obj.GetName()
        value = obj.GetItemText(obj.GetFirstSelected()) 

        if objName == 'selFile_lst':
            idx = obj.GetFirstSelected()
            # show selected image and the result of image processing with it 
            self.showImgProcRslt(self.fileList[idx])
        elif objName == 'proc_lst':
            pn = obj.GetItemText(obj.GetFirstSelected()) # process name 
            self.showHideProcParamWidgets(pn) # show parameter widgets         
    
    #-------------------------------------------------------------------
    
    def showHideProcParamWidgets(self, pn=''):
        """ Show wxPython widgets of parameters for a processing (pn),
        or hide them.

        Args:
            pn (str): Processing name

        Returns:
            None
        """
        if DEBUG: print("ImgProcsFrame.showHideProcParamWidgets()")

        flag = [] # list of True/False values to indicate show/hide widgets
        if pn != '':
        # processing name given, meaning to show the relevant parameters
            flag.append(True) # for showing processing name staticText
            nP = len(self.ipParams[pn]) # number of parameters
            for i in range(self.mNumParam):
                if i >= nP: flag.append(False)
                else: flag.append(True)
            flag.append(True) # for showing update button
        else:
        # no processing name given, meaning to hide widgets 
            flag.append(True) # for showing processing name staticText
            for i in range(self.mNumParam):
                flag.append(False) # for hiding parameter widgets
            flag.append(False) # for hiding update button

        ### show/hide widgets
        idx = 0
        w = wx.FindWindowByName("processName_sTxt", self.panel["ui"])
        if flag[idx]:
            w.SetLabel(pn)
            w.Show() # show process name
        else:
            w.Hide()
        for i in range(self.mNumParam):
            idx += 1
            w = wx.FindWindowByName("param%i_sTxt"%(i), self.panel["ui"])
            if flag[idx]: 
                w.Show() # show parameter description
                w.SetLabel(self.ipParamDesc[pn][i])
            else:
                w.Hide()
            w = wx.FindWindowByName("param%i_txt"%(i), self.panel["ui"])
            if flag[idx]:
                w.Show() # show parameter value
                w.SetValue(str(self.ipParamVal[pn][i]))
            else:
                w.Hide()
        idx += 1
        w = wx.FindWindowByName("updateParam_btn", self.panel["ui"])
        if flag[idx]: w.Show() # show update button
        else: w.Hide() # hide update button

        ### refresh gbs and panel
        self.gbs["ui"].Layout()
        self.panel["ui"].Layout()
        self.panel["ui"].SetupScrolling()
    
    #-------------------------------------------------------------------

    def onEnteredInTC(self, event):
        """ 'Enter' was pressed in wx.TextCtrl.

        Args: event (wx.Event)

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.onEnteredInTC()")
        
        obj = event.GetEventObject()
        objName = obj.GetName()
        
        if objName == 'targetFN_txt':
        # target file format has changed
            self.updateFileList()
    
    #-------------------------------------------------------------------
    
    def addFolders(self, dp):
        """ Adding sub-folders in the 'self.selectedFolders' list.

        Args:
            dp (str): Folder path to look for any other sub folders in it.

        Returns:
            None
        """
        if DEBUG: print("ImgProcsFrame.addFolders()")

        for fp in glob(path.join(dp, '*')):
        # go through everything in the selected folder
            if path.isdir(fp) == True: # this is a folder
                self.selectedFolders.append(fp) # add this sub-folder 
                self.addFolders(fp) # add folders in this sub-folder
    
    #-------------------------------------------------------------------
    
    def updateFileList(self):
        """ This function is called when selected folders or target file 
        name or extension has changed. 
        This function updates file list, which will be renamed.

        Args: None

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.updateFileList()")

        fL = []
        tcFN = wx.FindWindowByName("targetFN_txt", self.panel["ui"])
        fileForm = "%s"%(tcFN.GetValue()) 
        ### update self.fileList
        for dp in self.selectedFolders:
            p = path.join(dp, fileForm)
            for fp in glob(p):
                bn = path.basename(fp)
                ext = bn.split(".")[-1]
                if ext in self.extList:
                    fL.append(fp)
        self.fileList = fL

        ### update ListCtrl to show files to be processed 
        lc = wx.FindWindowByName("selFile_lst", self.panel["ui"])
        lc.DeleteAllItems() # delete the current contents
        for i, fp in enumerate(self.fileList):
            lc.Append([fp])
        self.showImgProcRslt()

    #-------------------------------------------------------------------
    
    def showImgProcRslt(self, fp=''):
        """ Show an image file and its result after image processing

        Args:
            fp (str): File path of image to show

        Returns:
            None
        """
        if DEBUG: print("ImgProcsFrame.showImgProcRslt()")

        if fp == '': fp = self.fileList[0]
        iImg = np.array(Image.open(fp))
        oImg = self.procImg(iImg.copy()) 

        ### draw image
        for i in range(2):
            if i == 0:
                img = iImg 
                k = "ip"
            elif i == 1:
                img = oImg 
                k = "op"
            if len(img.shape) > 2 and img.shape[2] == 4:
                wxImg = wx.ImageFromBuffer(img.shape[1], 
                                           img.shape[0], 
                                           img[:,:,:3].tostring(),
                                           img[:,:,3].tostring())
            else:
                wxImg = wx.ImageFromBuffer(img.shape[1], 
                                           img.shape[0], 
                                           img.tostring())
            w = wx.FindWindowByName("%s_sBmp"%(k), self.panel[k])
            w.SetBitmap(wx.Bitmap(wxImg))
            self.panel[k].SetupScrolling()
    
    #-------------------------------------------------------------------
    
    def procImg(self, img):
        """ Process with the given image

        Args:
            img (np.ndarray): Input image

        Return:
            img (np.ndarray): Output image
        """
        for pn in self.procList:
        # go through all planned processes 
            if pn == 'crop':
                x, y, w, h = self.ipParamVal[pn]
                img = img[y:y+h,x:x+w]
            elif pn == 'crop_ratio':
                x, y, w, h = self.ipParamVal[pn]
                x = int(x * img.shape[1])
                y = int(y * img.shape[0])
                w = int(w * img.shape[1])
                h = int(h * img.shape[0])
                img = img[y:y+h,x:x+w]
            elif pn == 'masking':
                fCol = self.ipParamVal[pn][0]
                ### load masking image
                maskImg = Image.open(self.maskFP)
                maskImg = maskImg.resize((img.shape[1],img.shape[0]))
                maskImg = np.array(maskImg)
                # sum r,g,b channel
                maskImg = np.sum(maskImg[:,:,0:3], axis=2)
                ### set fill color
                fCol = fCol.lstrip("#")
                c1 = int(fCol[:2], 16)
                c2 = int(fCol[2:4], 16)
                c3 = int(fCol[4:6], 16)
                if img.shape[2] == 3: fillCol = np.array([c1,c2,c3])
                elif img.shape[2] == 4: fillCol = np.array([c1,c2,c3,255])
                # delete (with fill color) black parts in masking image 
                img[maskImg==0] = fillCol 
            elif pn == 'resize':
                w, h = self.ipParamVal[pn]
                img = np.array(Image.fromarray(img).resize((w,h)))
            elif pn == 'resize_ratio':
                w, h = self.ipParamVal[pn]
                w = int(w * img.shape[1])
                h = int(h * img.shape[0])
                img = np.array(Image.fromarray(img).resize((w,h)))
            elif pn == 'rotate':
                value, expand = self.ipParamVal[pn]
                img = Image.fromarray(img)
                img = img.rotate(value, expand=expand)
                img = np.array(img)
            elif pn == 'flip':
                direction = self.ipParamVal[pn][0]
                img = Image.fromarray(img)
                ### 0:Image.FLIP_LEFT_RIGHT, 1:Image.FLIP_TOP_BOTTOM
                if direction == 2:
                    img = img.transpose(0)
                    img = img.transpose(1)
                else:
                    img = img.transpose(direction)
                img = np.array(img)
            elif pn in ['brighten', 'darken']:
                value = self.ipParamVal[pn][0]
                if value < 1: return img 
                if value > 255: value = 255
                if pn == 'darken': value = -value
                img = img.astype(np.int16)
                img += value
                img[img<0] = 0
                img[img>255] = 255
                img = img.astype(np.uint8)
            elif pn == 'text':
                txt, x, y, sz, col = self.ipParamVal[pn]
                x = int(x * img.shape[1])
                y = int(y * img.shape[0])
                img = Image.fromarray(img)
                draw = ImageDraw.Draw(img)
                if sys.platform == "darwin":
                    fontFP = "/System/Library/Fonts/Monaco.dfont"
                elif sys.platform.startswith("win"):
                    fontFP = "/Windows/Fonts/cour.ttf"
                font = ImageFont.truetype(font=fontFP, size=sz)
                draw.text((x, y), txt, col, font=font)
                img = np.array(img)
        return img
    
    #-------------------------------------------------------------------

    def runImgProc(self):
        """ Run image processing going through all files 
        with all planned processing 
        
        Args: None

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.runImgProc()")

        msg = "Processed files -----\n\n" # result message 
        msg4log = "" # log message
        for i, fp in enumerate(self.fileList):
            img = np.array(Image.open(fp)) # open image
            img = self.procImg(img) # process
            Image.fromarray(img).save(fp) # save image
            pl = str(self.procList)
            pl = pl.strip("[]").replace(", ","/").replace("'","")
            msg4log += "%s, %s, %s\n"%(get_time_stamp(), fp, pl)
            msg += "%s\n\n"%(fp)

        writeFile(self.logFile, msg4log) # logging results
        wx.MessageBox(msg, 'Results', wx.OK)

    #-------------------------------------------------------------------

    def onClose(self, event):
        """ Close this frame.

        Args: event (wx.Event)

        Returns: None
        """
        if DEBUG: print("ImgProcsFrame.onClose()")

        for k in self.timer.keys():
            if isinstance(self.timer[k], wx.Timer):
                self.timer[k].Stop()
        self.Destroy()

    #-------------------------------------------------------------------

#=======================================================================

class ImgProcsApp(wx.App):
    """ Initializing ImgProcs app with ImgProcsFrame.

    Attributes:
        frame (wx.Frame): ImgProcsFrame.
    """
    def OnInit(self):
        if DEBUG: print("ImgProcsApp.OnInit()")
        self.frame = ImgProcsFrame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

#=======================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '-w': GNU_notice(1)
        elif sys.argv[1] == '-c': GNU_notice(2)
    else:
        GNU_notice(0)
        app = ImgProcsApp(redirect = False)
        app.MainLoop()
