from functools import partial

from PySide6.QtCore import Qt, Slot, QObject, QDateTime
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from jal.db.helpers import load_icon
from jal.ui.reports.ui_holdings_report import Ui_HoldingsWidget
from jal.reports.reports import Reports
from jal.db.asset import JalAsset
from jal.db.holdings_model import HoldingsModel
from jal.widgets.mdi import MdiWidget
from jal.db.tax_estimator import TaxEstimator
from jal.widgets.price_chart import ChartWindow

JAL_REPORT_CLASS = "HoldingsReport"


# ----------------------------------------------------------------------------------------------------------------------
class HoldingsReport(QObject):
    def __init__(self):
        super().__init__()
        self.name = self.tr("Holdings")
        self.window_class = "HoldingsReportWindow"


# ----------------------------------------------------------------------------------------------------------------------
class HoldingsReportWindow(MdiWidget):
    def __init__(self, parent: Reports, settings: dict = None):
        super().__init__(parent.mdi_area())
        self.ui = Ui_HoldingsWidget()
        self.ui.setupUi(self)
        self._parent = parent
        self.name = self.tr("Holdings")

        # Add available groupings
        self.ui.GroupCombo.addItem(self.tr("Currency - Account - Asset"), "currency_id;account_id;asset_id")
        self.ui.GroupCombo.addItem(self.tr("Asset - Account"), "asset_id;account_id")

        self.holdings_model = HoldingsModel(self.ui.HoldingsTreeView)
        self.ui.HoldingsTreeView.setModel(self.holdings_model)
        # self.holdings_model.configureView()
        self.ui.HoldingsTreeView.setContextMenuPolicy(Qt.CustomContextMenu)

        self.connect_signals_and_slots()

        # Setup holdings parameters
        current_time = QDateTime.currentDateTime()
        current_time.setTimeSpec(Qt.UTC)  # We use UTC everywhere so need to force TZ info
        self.ui.HoldingsDate.setDateTime(current_time)
        self.ui.HoldingsCurrencyCombo.setIndex(JalAsset.get_base_currency())

    def connect_signals_and_slots(self):
        self.ui.HoldingsDate.dateChanged.connect(self.ui.HoldingsTreeView.model().setDate)
        self.ui.HoldingsCurrencyCombo.changed.connect(self.ui.HoldingsTreeView.model().setCurrency)
        self.ui.HoldingsTreeView.customContextMenuRequested.connect(self.onHoldingsContextMenu)
        self.ui.GroupCombo.currentIndexChanged.connect(self.onGroupingChange)
        self.ui.SaveButton.pressed.connect(partial(self._parent.save_report, self.name, self.ui.HoldingsTreeView.model()))

    @Slot()
    def onGroupingChange(self, idx):
        self.ui.HoldingsTreeView.model().setGrouping(self.ui.GroupCombo.itemData(idx))

    @Slot()
    def onHoldingsContextMenu(self, pos):
        index = self.ui.HoldingsTreeView.indexAt(pos)
        contextMenu = QMenu(self.ui.HoldingsTreeView)
        actionShowChart = QAction(icon=load_icon("chart.png"), text=self.tr("Show Price Chart"), parent=self.ui.HoldingsTreeView)
        actionShowChart.triggered.connect(partial(self.showPriceChart, index))
        contextMenu.addAction(actionShowChart)
        tax_submenu = contextMenu.addMenu(load_icon("tax.png"), self.tr("Estimate tax"))
        actionEstimateTaxPt = QAction(text=self.tr("Portugal"), parent=self.ui.HoldingsTreeView)
        actionEstimateTaxPt.triggered.connect(partial(self.estimateRussianTax, index, 'pt'))
        tax_submenu.addAction(actionEstimateTaxPt)
        actionEstimateTaxRu = QAction(text=self.tr("Russia"), parent=self.ui.HoldingsTreeView)
        actionEstimateTaxRu.triggered.connect(partial(self.estimateRussianTax, index, 'ru'))
        tax_submenu.addAction(actionEstimateTaxRu)
        contextMenu.popup(self.ui.HoldingsTreeView.viewport().mapToGlobal(pos))

    @Slot()
    def showPriceChart(self, index):
        model = index.model()
        account, asset, currency, asset_qty = model.get_data_for_tax(index)
        self._parent.mdi_area().addSubWindow(ChartWindow(account, asset, currency, asset_qty))

    @Slot()
    def estimateRussianTax(self, index, country_code):
        model = index.model()
        account, asset, currency, asset_qty = model.get_data_for_tax(index)
        self._parent.mdi_area().addSubWindow(TaxEstimator(country_code, account, asset, asset_qty), size=(1000, 300))
