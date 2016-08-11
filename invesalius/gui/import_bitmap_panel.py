#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------
import wx
import wx.gizmos as gizmos
from wx.lib.pubsub import pub as Publisher
import wx.lib.splitter as spl

import constants as const
import gui.dialogs as dlg
import bitmap_preview_panel as bpp
import reader.bitmap_reader as bpr
from dialogs import ImportBitmapParameters

myEVT_SELECT_SERIE = wx.NewEventType()
EVT_SELECT_SERIE = wx.PyEventBinder(myEVT_SELECT_SERIE, 1)

myEVT_SELECT_SLICE = wx.NewEventType()
EVT_SELECT_SLICE = wx.PyEventBinder(myEVT_SELECT_SLICE, 1)

myEVT_SELECT_PATIENT = wx.NewEventType()
EVT_SELECT_PATIENT = wx.PyEventBinder(myEVT_SELECT_PATIENT, 1)

myEVT_SELECT_SERIE_TEXT = wx.NewEventType()
EVT_SELECT_SERIE_TEXT = wx.PyEventBinder(myEVT_SELECT_SERIE_TEXT, 1)

class SelectEvent(wx.PyCommandEvent):
    def __init__(self , evtType, id):
        super(SelectEvent, self).__init__(evtType, id)

    def GetSelectID(self):
        return self.SelectedID

    def SetSelectedID(self, id):
        self.SelectedID = id

    def GetItemData(self):
        return self.data

    def SetItemData(self, data):
        self.data = data


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, pos=wx.Point(5, 5))#,
                          #size=wx.Size(280, 656))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(InnerPanel(self), 1, wx.EXPAND|wx.GROW|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Layout()
        self.Update()
        self.SetAutoLayout(1)


# Inner fold panel
class InnerPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, pos=wx.Point(5, 5))#,
                          #size=wx.Size(680, 656))

        self.patients = []
        self.first_image_selection = None
        self.last_image_selection = None
        self._init_ui()
        self._bind_events()
        self._bind_pubsubevt()

    def _init_ui(self):
        splitter = spl.MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetOrientation(wx.VERTICAL)
        self.splitter = splitter

        panel = wx.Panel(self)
        self.btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, _("Import"))

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(self.btn_ok)
        btnsizer.AddButton(self.btn_cancel)
        btnsizer.Realize()

        self.combo_interval = wx.ComboBox(panel, -1, "", choices=const.IMPORT_INTERVAL,
                                     style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.combo_interval.SetSelection(0)

        inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
        inner_sizer.AddSizer(btnsizer, 0, wx.LEFT|wx.TOP, 5)
        inner_sizer.Add(self.combo_interval, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        panel.SetSizer(inner_sizer)
        inner_sizer.Fit(panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 20, wx.EXPAND)
        sizer.Add(panel, 0, wx.EXPAND|wx.LEFT, 90)

        self.text_panel = TextPanel(splitter)
        splitter.AppendWindow(self.text_panel, 250)

        self.image_panel = ImagePanel(splitter)
        splitter.AppendWindow(self.image_panel, 250)
        
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Layout()
        self.Update()
        self.SetAutoLayout(1)

    def _bind_pubsubevt(self):
        Publisher.subscribe(self.ShowBitmapPreview, "Load import bitmap panel")
        Publisher.subscribe(self.GetSelectedImages ,"Selected Import Images")  

    def ShowBitmapPreview(self, pubsub_evt):
        data = pubsub_evt.data
        #self.patients.extend(dicom_groups)
        self.text_panel.Populate(data)

    def GetSelectedImages(self, pubsub_evt):
        self.first_image_selection = pubsub_evt.data[0]
        self.last_image_selection = pubsub_evt.data[1]
        
    def _bind_events(self):
        self.Bind(EVT_SELECT_SERIE, self.OnSelectSerie)
        self.Bind(EVT_SELECT_SLICE, self.OnSelectSlice)
        self.Bind(EVT_SELECT_PATIENT, self.OnSelectPatient)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.OnClickOk)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.OnClickCancel)
        self.text_panel.Bind(EVT_SELECT_SERIE_TEXT, self.OnDblClickTextPanel)

    def OnSelectSerie(self, evt):
        #patient_id, serie_number = evt.GetSelectID()
        #self.text_panel.SelectSerie(evt.GetSelectID())
        #for patient in self.patients:
        #    if patient_id == patient.GetDicomSample().patient.id:
        #        for group in patient.GetGroups():
        #            if serie_number == group.GetDicomSample().acquisition.serie_number:
        #                self.image_panel.SetSerie(group)

        pass



    def OnSelectSlice(self, evt):
        pass

    def OnSelectPatient(self, evt):
        pass

    def OnDblClickTextPanel(self, evt):
        group = evt.GetItemData()
        self.LoadDicom(group)

    def OnClickOk(self, evt):
        parm = dlg.ImportBitmapParameters()
        parm.SetInterval(self.combo_interval.GetSelection())
        parm.ShowModal()

        group = self.text_panel.GetSelection()
        if group:
            self.LoadDicom(group)

    def OnClickCancel(self, evt):
        Publisher.sendMessage("Cancel DICOM load")

    def LoadDicom(self, group):
        #interval = self.combo_interval.GetSelection()
        #if not isinstance(group, dcm.DicomGroup):
        #    group = max(group.GetGroups(), key=lambda g: g.nslices)
        
        #slice_amont = group.nslices
        #if (self.first_image_selection != None) and (self.first_image_selection != self.last_image_selection):
        #    slice_amont = (self.last_image_selection) - self.first_image_selection
        #    slice_amont += 1
        #    if slice_amont == 0:
        #        slice_amont = group.nslices

        #nslices_result = slice_amont / (interval + 1)
        #if (nslices_result > 1):
        #    Publisher.sendMessage('Open DICOM group', (group, interval, 
        #                            [self.first_image_selection, self.last_image_selection]))
        #else:
        #    dlg.MissingFilesForReconstruction()
        pass


class TextPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent

        self._selected_by_user = True
        self.idserie_treeitem = {}
        self.treeitem_idpatient = {}

        self.selected_item = None

        self.__init_gui()
        self.__bind_events_wx()
        self.__bind_pubsub_evt()

    def __bind_pubsub_evt(self):
        Publisher.subscribe(self.SelectSeries, 'Select series in import panel')

    def __bind_events_wx(self):
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

    def __init_gui(self):
        tree = gizmos.TreeListCtrl(self, -1, style =
                                   wx.TR_DEFAULT_STYLE
                                   | wx.TR_HIDE_ROOT
                                   | wx.TR_ROW_LINES
                                   | wx.TR_COLUMN_LINES
                                   | wx.TR_FULL_ROW_HIGHLIGHT
                                   | wx.TR_SINGLE
                                   | wx.TR_HIDE_ROOT
                                   )


        tree.AddColumn(_("Path"))
        tree.AddColumn(_("Type"))
        tree.AddColumn(_("Width x Height"))

        tree.SetMainColumn(0)
        tree.SetColumnWidth(0, 880)
        tree.SetColumnWidth(1, 60)
        tree.SetColumnWidth(2, 130)

        self.root = tree.AddRoot(_("InVesalius Database"))
        self.tree = tree

    def OnKeyPress(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_DELETE or key_code == wx.WXK_NUMPAD_DELETE:
            if self.selected_item != self.tree.GetRootItem():
                text_item = self.tree.GetItemText(self.selected_item)
                
                index = bpr.BitmapData().GetIndexByPath(text_item)

                bpr.BitmapData().RemoveFileByPath(text_item)

                data_size = len(bpr.BitmapData().GetData())
                
                if index >= 0 and index < data_size:
                    Publisher.sendMessage('Set bitmap in preview panel', index)
                elif index == data_size and data_size > 0:
                    Publisher.sendMessage('Set bitmap in preview panel', index - 1)
                elif data_size == 1:
                    Publisher.sendMessage('Set bitmap in preview panel', 0)
                else:
                    Publisher.sendMessage('Show black slice in single preview image')
                
                self.tree.Delete(self.selected_item)
                self.tree.Update()
                self.tree.Refresh()
                Publisher.sendMessage('Remove preview panel', text_item)
        evt.Skip()

    def SelectSeries(self, pubsub_evt):
        group_index = pubsub_evt.data

    def Populate(self, data):
        tree = self.tree
        for value in data:
            parent = tree.AppendItem(self.root, value[0])
            self.tree.SetItemText(parent, value[2], 1)
            self.tree.SetItemText(parent, value[5], 2)

        tree.Expand(self.root)
        #tree.SelectItem(parent_select)
        tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate)
        tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

        Publisher.sendMessage('Load bitmap into import panel', data)

    def OnSelChanged(self, evt):
        item = self.tree.GetSelection()
        if self._selected_by_user:
            self.selected_item = item
            
            text_item = self.tree.GetItemText(self.selected_item)
            index = bpr.BitmapData().GetIndexByPath(text_item)
            Publisher.sendMessage('Set bitmap in preview panel', index)

        evt.Skip()

    def OnActivate(self, evt):
        item = evt.GetItem()
        group = self.tree.GetItemPyData(item)
        my_evt = SelectEvent(myEVT_SELECT_SERIE_TEXT, self.GetId())
        my_evt.SetItemData(group)
        self.GetEventHandler().ProcessEvent(my_evt)

    def OnSize(self, evt):
        self.tree.SetSize(self.GetSize())
        evt.Skip()

    def SelectSerie(self, serie):
        self._selected_by_user = False
        item = self.idserie_treeitem[serie]
        self.tree.SelectItem(item)
        self._selected_by_user = True

    def GetSelection(self):
        """Get selected item"""
        item = self.tree.GetSelection()
        group = self.tree.GetItemPyData(item)
        return group


class ImagePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self._init_ui()
        self._bind_events()

    def _init_ui(self):
        splitter = spl.MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetOrientation(wx.HORIZONTAL)
        self.splitter = splitter

        splitter.ContainingSizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.text_panel = SeriesPanel(splitter)
        splitter.AppendWindow(self.text_panel, 600)

        self.image_panel = SlicePanel(splitter)
        splitter.AppendWindow(self.image_panel, 250)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Layout()
        self.Update()
        self.SetAutoLayout(1)

    def _bind_events(self):
        self.text_panel.Bind(EVT_SELECT_SERIE, self.OnSelectSerie)
        self.text_panel.Bind(EVT_SELECT_SLICE, self.OnSelectSlice)

    def OnSelectSerie(self, evt):
        evt.Skip()

    def OnSelectSlice(self, evt):
        self.image_panel.bitmap_preview.ShowSlice(evt.GetSelectID())
        evt.Skip()

    def SetSerie(self, serie):
        self.image_panel.bitmap_preview.SetDicomGroup(serie)


class SeriesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        #self.SetBackgroundColour((0,0,0))

        self.thumbnail_preview = bpp.BitmapPreviewSeries(self)
        #self.bitmap_preview = bpp.BitmapPreviewSlice(self)
        #self.bitmap_preview.Show(0)
        

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.thumbnail_preview, 1, wx.EXPAND | wx.ALL, 5)
        #self.sizer.Add(self.bitmap_preview, 1, wx.EXPAND | wx.ALL, 5)
        self.sizer.Fit(self)

        self.SetSizer(self.sizer)

        self.Layout()
        self.Update()
        self.SetAutoLayout(1)

        self.__bind_evt()
        self._bind_gui_evt()

    def __bind_evt(self):
        #Publisher.subscribe(self.ShowDicomSeries, 'Load bitmap preview')
        #Publisher.subscribe(self.SetDicomSeries, 'Load group into import panel')
        Publisher.subscribe(self.SetBitmapFiles, 'Load bitmap into import panel')

    def _bind_gui_evt(self):
        self.thumbnail_preview.Bind(bpp.EVT_CLICK_SERIE, self.OnSelectSerie)
        #self.bitmap_preview.Bind(bpp.EVT_CLICK_SLICE, self.OnSelectSlice)

    #def SetDicomSeries(self, pubsub_evt):
    #    group = pubsub_evt.data
    #    self.bitmap_preview.SetDicomGroup(group)
    #    self.bitmap_preview.Show(1)
    #    self.thumbnail_preview.Show(0)
    #    self.sizer.Layout()
    #    self.Update()

    def GetSelectedImagesRange(self):
        return [self.bitmap_preview.first_selected, self.dicom_preview_last_selection]

    def SetBitmapFiles(self, pubsub_evt):


        bitmap = pubsub_evt.data
        #self.bitmap_preview.Show(0)
        self.thumbnail_preview.Show(1)

        self.thumbnail_preview.SetBitmapFiles(bitmap)
        #self.bitmap_preview.SetPatientGroups(patient)

        self.Update()

    def OnSelectSerie(self, evt):
        data = evt.GetItemData()
        my_evt = SelectEvent(myEVT_SELECT_SERIE, self.GetId())
        my_evt.SetSelectedID(evt.GetSelectID())
        my_evt.SetItemData(evt.GetItemData())
        self.GetEventHandler().ProcessEvent(my_evt)

        #self.bitmap_preview.SetDicomGroup(data)
        #self.bitmap_preview.Show(1)
        #self.thumbnail_preview.Show(0)
        self.sizer.Layout()
        self.Show()
        self.Update()

    def OnSelectSlice(self, evt):
        my_evt = SelectEvent(myEVT_SELECT_SLICE, self.GetId())
        my_evt.SetSelectedID(evt.GetSelectID())
        my_evt.SetItemData(evt.GetItemData())
        self.GetEventHandler().ProcessEvent(my_evt)


    #def ShowDicomSeries(self, pubsub_evt):
    #    patient = pubsub_evt.data
    #    if isinstance(patient, dcm.PatientGroup):
    #        self.thumbnail_preview.SetPatientGroups(patient)
    #        self.bitmap_preview.SetPatientGroups(patient)


class SlicePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.__init_gui()
        self.__bind_evt()

    def __bind_evt(self):
        #Publisher.subscribe(self.ShowDicomSeries, 'Load bitmap preview')
        #Publisher.subscribe(self.SetDicomSeries, 'Load group into import panel')
        Publisher.subscribe(self.SetBitmapFiles, 'Load bitmap into import panel')

    def __init_gui(self):
        self.SetBackgroundColour((255,255,255))
        self.bitmap_preview = bpp.SingleImagePreview(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bitmap_preview, 1, wx.GROW|wx.EXPAND)
        sizer.Fit(self)
        self.SetSizer(sizer)
        self.Layout()
        self.Update()
        self.SetAutoLayout(1)
        self.sizer = sizer

    def SetBitmapFiles(self, pubsub_evt):
        data = pubsub_evt.data
        self.bitmap_preview.SetBitmapFiles(data)
        self.sizer.Layout()
        self.Update()

    #def SetDicomSeries(self, evt):
    #    group = evt.data
    #    self.bitmap_preview.SetDicomGroup(group)
    #    self.sizer.Layout()
    #    self.Update()

    #def ShowDicomSeries(self, pubsub_evt):
    #    patient = pubsub_evt.data
    #    group = patient.GetGroups()[0]
    #    self.bitmap_preview.SetDicomGroup(group)
    #    self.sizer.Layout()
    #    self.Update()

