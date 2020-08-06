import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QEvent, QSize, QPoint, QRectF

from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtGui import QPixmap, QPen, QBrush
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
                             QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
                             QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget, QListWidget, QTableView, QAbstractItemView, QFileDialog,
                             QGraphicsPixmapItem, QGraphicsRectItem)

from os import listdir, path
from pathlib import Path
from os.path import isfile, join
import pandas as pd
import numpy as np
import os


# class FileDialog(QFileDialog):


class PFileModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """

    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        # if not(index.isValid()):
        #    return None
        if role == Qt.DisplayRole:
            column = index.column()
            row = index.row()
            retstr = self._data.iloc[index.row(), index.column()]
            if retstr != retstr:
                return "nan"
            return str(retstr)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        # if index.isValid() & role == Qt.EditRole:
        if index.isValid():
            row = index.row()
            col = index.column()
            df = self._data
            if index.column() > 0:
                self._data.iloc[row, col] = str(value)
            else:
                return False;

            self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])
            return True
        return False

    def getRowData(self, index):
        if index.isValid():
            rowdata = self._data.loc[[index.row()]]
            return rowdata
        return None

    def getImageInfo(self, indexes):
        index = indexes[0]
        if index.isValid():
            imgInfo = ImageInfo()
            rowdata = self._data.loc[[index.row()]]
            imgInfo.updateInfo(rowdata.iloc[0]['Filename'], rowdata.iloc[0]['BoxIndex'], rowdata.iloc[0]['Gbox'])
            return imgInfo
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def getDataFrame(self):
        return self._data

    def updateDataFrame(self, df):
        self.beginResetModel()
        self._data = df
        '''
        Needs ability to merge
        for index, row in df.iterrows():
            fname=row['Filename']
            if self._data[self._data['Filename'].str.contains(fname):
                print(row['c1'], row['c2'])
        '''
        self.endResetModel()


class ImageInfo():

    def __init__(self, filename=None, gbox=None, boxindex=None):
        if filename == None:
            self.filename = ""
            self.gbox = QtCore.QRect()
            self.boxindex = ""
        self.updateInfo(filename, gbox, boxindex)

    def setFilename(self, filename):
        self.filename = filename

    def reset(self):
        self.filename = ""
        self.gbox = ""
        self.boxindex = ""

    def updateInfo(self, filename, boxindex, gbox):
        self.filename = filename
        self.gbox = gbox
        self.boxindex = boxindex
        if gbox == "":
            self.gbox = QtCore.QRect()

    def getGbox(self):
        # TODO: Needs to be saved in image Format

        gbox = QtCore.QRect()
        if self.gbox == "" or self.gbox != self.gbox:
            return QtCore.QRect()
        li = self.gbox[1:-1].split(',')
        tli = list(map(int, li))
        return QtCore.QRect(*tli)


class FileTable(QTableView):
    def __init__(self):
        super().__init__()

        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setDefaultSectionSize(6)
        self.setShowGrid(False)
        # self.resizeRowsToContents()
        # elf.resizeColumnsToContents()

    def setModel(self, model):
        super().setModel(model)
        self.setColumnWidth(1, 4)
        self.setColumnWidth(2, 2)
        self.setColumnWidth(3, 2)
        self.verticalHeader().setDefaultSectionSize(6)
        # self.resizeColumnsToContents()
        # self.resizeRowsToContents()
        # self.verticalHeader().setDefaultSectionSize(10)


class ImageView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene())
        rootpath = "C:\\Users\\ekambulow\\PycharmProjects\\QtImageboxer\\"
        filename = 'data\\python.png'
        self.item = QGraphicsPixmapItem(QPixmap(rootpath + filename))
        self.scene().addItem(self.item)
        self.rect_item = QGraphicsRectItem(QRectF(), self.item)
        self.rect_item.setPen(QPen(QtGui.QColor(51, 153, 255), 2, Qt.SolidLine))
        self.rect_item.setBrush(QBrush(QtGui.QColor(0, 255, 0, 40)))

    def mousePressEvent(self, event):
        self.pi = self.mapToScene(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pf = self.mapToScene(event.pos())
        if (self.pi - pf).manhattanLength() > QApplication.startDragDistance():
            self.pf = pf
            self.draw_rect()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        pf = self.mapToScene(event.pos())
        if (self.pi - pf).manhattanLength() > QApplication.startDragDistance():
            self.pf = pf
            self.draw_rect()
        super().mouseReleaseEvent(event)

    def draw_rect(self):
        r = QRectF(self.pi, self.pf).normalized()
        r = self.rect_item.mapFromScene(r).boundingRect()
        self.rect_item.setRect(r)


class ImageBoxer(QtWidgets.QWidget):
    BoxSelected = QtCore.pyqtSignal()

    def __init__(self, imgdir):
        super().__init__()

        selBox = QtCore.QRect()

        self.setGeometry(30, 30, 600, 400)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.drawbegin = QtCore.QPoint()
        self.drawend = QtCore.QPoint()
        self.pixmapsize=QSize()
        self.screenpixmapsize=QSize()

        self.imgInfo = ImageInfo()
        # self.initUI()
        self.imgdir = imgdir
        self.loadimage()
        self.show()

    def updateImageBox(self, imgInfo):
        self.imgInfo.gbox = imgInfo.gbox
        self.imgInfo.boxindex = imgInfo.boxindex
        self.setBox(self.imgInfo.getGbox())

    def updateImage(self, imgInfo):
        self.imgInfo.gbox = imgInfo.gbox
        # if self.imgInfo.gbox!=self.imgInfo.gbox:
        #    self.imgInfo.gbox=QtCore.QRect()
        self.imgInfo.boxindex = imgInfo.boxindex
        self.imgInfo.filename = imgInfo.filename
        if self.imgInfo.filename== "":
            self.loadimage()
        else:
            imgpath = self.imgdir + '/' + imgInfo.filename
            self.loadimage(imgpath)
        self.setBox(self.imgInfo.getGbox())

    def loadimage(self, filepath=None):
        # filepath = 'data/test.JPG'
        if filepath == None:
            filepath = 'data/python.png'
        pixmap = QPixmap(filepath)
        self.pixmapsize = pixmap.size()
        # smaller_pixmap = pixmap.scaled(32, 32, PyQt5.QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
        # self.smaller_pixmap = pixmap.scaled(640, 480)
        self.smaller_pixmap = pixmap

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.drawPixmap(self.rect(), self.smaller_pixmap)
        br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 40))
        qp.setBrush(br)
        qp.drawRect(QtCore.QRect(self.drawbegin, self.drawend))

        qp.setPen(Qt.black)
        # qp.DrawText(0,20,self.imgInfo.boxindex)
        qp.drawText(0, 20, self.imgInfo.boxindex)
        # print("Painted", self.imgInfo.boxindex)

    def setBox(self, rect):
        self.begin = rect.topLeft()
        self.end = rect.bottomRight()

        # TODO: Convert to screen coords
        drawrect=self.pixmaptoScreenRect(rect)
        #self.drawbegin=drawrect.topLeft()
        #self.drawend=drawrect.bottomRight()
        self.drawbegin = self.begin
        self.drawend = self.end

        self.update()

    def screentoPixmapRect(self,rect):
        # TODO: Verify Convert from screen to Pixmap
        hratio=self.pixmapsize.height()/self.screenpixmapsize.height()
        wratio=self.pixmapsize.width()/self.screenpixmapsize.width()
        tl=QtCore.QPoint(rect.topLeft().x()*hratio,rect.topLeft().y()*wratio)
        br=QtCore.QPoint(rect.bottomRight().x()*hratio,rect.bottomRight().y()*wratio)
        pmrect=QtCore.QRect(tl,br)
        return pmrect

    def pixmaptoScreenRect(self,rect):
        # TODO: Verify Convert from screen to Pixmap
        hratio=self.pixmapsize.height()/self.screenpixmapsize.height()
        wratio=self.pixmapsize.width()/self.screenpixmapsize.width()
        tl=QtCore.QPoint(rect.topLeft().x()/hratio,rect.topLeft().y()/wratio)
        br=QtCore.QPoint(rect.bottomRight().x()*hratio,rect.bottomRight().y()*wratio)
        screenrect=QtCore.QRect(tl,br)
        return screenrect

    def mousePressEvent(self, event):
        self.drawbegin = event.pos()
        self.drawend = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.drawend = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.drawend = event.pos()
        # TODO: Verify Convert from screen coords
        screenrect=QtCore.QRect(self.drawbegin, self.drawend)
        self.SelBox =self.screentoPixmapRect(screenrect)
        self.SelBox = QtCore.QRect(self.drawbegin, self.drawend)
        self.begin = self.SelBox.topLeft()
        self.end = self.SelBox.bottomRight()

        self.BoxSelected.emit()
        # TODO: Add Text to Selected Item
        self.update()


class IndexComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.installEventFilter((self))
        self.setEditable(True)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete:
                self.removeItem(self.currentIndex())
                return True
        return QComboBox.eventFilter(self, obj, event)


class SelBoxerWidget(QDialog):
    def __init__(self, parent=None):
        super(SelBoxerWidget, self).__init__(parent)
        self.title = 'Image Boxer'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 640
        self.resize(720, 480)
        self.originalPalette = QApplication.palette()

        self.imgInfo = ImageInfo()

        self.filename = " Test"
        self.selbox = QtCore.QRect()
        self.createSelectionGroupBox()
        self.fname_json = 'ai_index.json'

        home_dir = str(Path.home())
        start_path2 = "C:/Users/ekambulow/PycharmProjects/joelskeras/data/"
        start_path3 = "./data/"
        start_path = "/Users/ekambulow/PycharmProjects/joelskeras"
        # self.imgDirectory=QFileDialog.getExistingDirectory(self,"Open Directory",start_path3,QFileDialog.ShowDirsOnly)
        abs_path=os.path.abspath(start_path3)
        self.imgDirectory = abs_path
        fldf = self.createFilelist(self.imgDirectory)
        self.fmodel = PFileModel(fldf)
        self.fileTab = FileTable()
        self.fileTab.setModel(self.fmodel)
        self.fileTab.clicked.connect(self.onFileSelected)
        self.createFileGroupBox()

        leftLayout = QVBoxLayout()
        self.ImageBox = ImageBoxer(self.imgDirectory)
        self.ImageBox.BoxSelected.connect(self.onBoxSelected)
        leftLayout.addWidget(self.ImageBox)
        leftLayout.addWidget(self.SelectionGroupBox)
        leftLayout.setStretch(0, 2)
        leftLayout.setStretch(1, 1)

        midLayout = QHBoxLayout()
        midLayout.addLayout(leftLayout)
        midLayout.addWidget(self.FileGroupBox)
        midLayout.setStretch(0, 1)
        midLayout.setStretch(1, 1)
        # midLayout.setColumnStretch(0, 1)
        # midLayout.setColumnStretch(1, 1)

        mainLayout = QGridLayout()
        # mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addLayout(midLayout, 1, 0)

        self.setLayout(mainLayout)

    def onBoxSelected(self):
        if self.imgInfo.filename == None:
            self.ImageBox.setBox(QtCore.QRect())
            return
        self.selbox = self.ImageBox.SelBox
        self.imgInfo.gbox = self.selbox.getRect()
        rect = self.selbox.getRect()
        self.boxlab.setText(str(rect))
        indexes = self.fileTab.selectedIndexes()
        indtext = self.indexComboBox.currentText()
        self.fmodel.setData(indexes[1], str(indtext))
        self.fmodel.setData(indexes[2], str(rect))
        print(indtext, str(rect))
        self.boxlab.update()

    def onFileSelected(self):

        sender = self.sender()
        indexes = sender.selectedIndexes()
        for ind in indexes:
            data = self.fmodel.data(ind)
            print(" ", data)
        # row=indexes[0].row()
        self.imgInfo = self.fmodel.getImageInfo(indexes)
        self.ImageBox.updateImage(self.imgInfo)
        # self.imgInfo=self.fmodel.data(indexes[0])
        self.flab.setText("File: " + self.imgInfo.filename)
        self.boxlab.setText("Coord: " + str(self.imgInfo.gbox))

    def createFilelist(self, imgdir):
        df = pd.DataFrame(columns=['Filename', 'BoxIndex', 'Gbox'])
        mypath = "/"
        ext = ['png', 'jpg', 'gif']
        ext = [e.upper() for e in ext]
        onlyfiles = []
        # onlyfiles = [f for f in listdir(imgdir) if isfile(join(imgdir, f))]
        img_files = [f for f in listdir(imgdir) if f.upper().endswith(tuple(ext))]
        fl = np.asarray(img_files)
        df['Filename'] = fl
        df['BoxIndex'] = ""
        df['Gbox'] = np.nan
        return df

    def saveModeltoFile(self):
        fname = self.imgDirectory + '/' + self.fname_json
        df = self.fmodel.getDataFrame()
        df.to_json(fname)

    def loadJSONtoModel(self):
        fname = self.imgDirectory + '/' + self.fname_json
        df = pd.read_json(fname)
        self.fmodel.updateDataFrame(df)  # anything not in

    def createFileGroupBox(self):
        editLayout = QHBoxLayout()
        self.dirEdit = QLineEdit()
        self.butDir = QPushButton("...")
        editLayout.addWidget(self.dirEdit)
        editLayout.addWidget(self.butDir)

        self.dirEdit.setText(self.imgDirectory)
        self.FileGroupBox = QGroupBox("File Group ")
        butLayout = QHBoxLayout()
        self.butSave = QPushButton("Save")
        self.butLoad = QPushButton("Load")
        self.butLoad.setEnabled(False)
        self.butLoad.released.connect(self.onLoadPushed)
        self.butSave.released.connect(self.onSavePushed)
        self.dirEdit.returnPressed.connect(self.onDirChanged)
        self.butDir.released.connect(self.onSeldDirPushed)
        butLayout.addWidget(self.butSave)
        butLayout.addWidget(self.butLoad)
        layout = QVBoxLayout()
        layout.addLayout(editLayout)
        layout.addWidget(self.dirEdit)
        layout.addWidget(self.fileTab)
        layout.addLayout(butLayout)
        # layout.addStretch(1)
        self.FileGroupBox.setLayout(layout)

    def onSeldDirPushed(self):
        self.imgDirectory = QFileDialog.getExistingDirectory(self, "Open Directory", self.imgDirectory,
                                                             QFileDialog.ShowDirsOnly)
        self.dirEdit.setText(self.imgDirectory)
        self.onDirChanged()

    def onDirChanged(self):
        self.imgDirectory = self.dirEdit.text()
        self.checkDirforJSON()
        fldf = self.createFilelist(self.imgDirectory)
        self.fmodel.updateDataFrame(fldf)
        self.imgInfo.reset()
        self.ImageBox.updateImage(self.imgInfo)


    def checkDirforJSON(self):
        json_path = self.imgDirectory + '/' + self.fname_json
        if os.path.isfile(json_path):
            self.butLoad.setEnabled(True)
            return True
        else:
            self.butLoad.setEnabled(False)
            return False
        pass


    def onLoadPushed(self):
        # TODO Load JSON
        pass

    def onSavePushed(self):
        self.saveModeltoFile()
        self.checkDirforJSON()


    def createSelectionGroupBox(self):
        self.SelectionGroupBox = QGroupBox("Selection Info")
        indexdict = {"one": 1, "two": 2, 'three': 3}
        # self.indexComboBox = QComboBox()
        self.indexComboBox = IndexComboBox()
        SelectionTable = QTableWidget(2, 2)
        self.flab = QLabel()
        self.boxlab = QLabel()
        self.flab.setText("Filename" + self.filename)
        self.boxlab.setText("Sel Box" + " (None)")
        self.indexComboBox.addItems(indexdict.keys())
        layout = QVBoxLayout()
        layout.addWidget(self.flab)
        layout.addWidget(self.indexComboBox)
        layout.addWidget(self.boxlab)

        self.SelectionGroupBox.setLayout(layout)

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


# if __name__ == '__main__':
#    app = QtWidgets.QApplication(sys.argv)
#    window = MyWidget()
#    window.show()
#    app.aboutToQuit.connect(app.deleteLater)
#    sys.exit(app.exec_())

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    gallery = SelBoxerWidget()
    gallery.show()
    sys.exit(app.exec_())
