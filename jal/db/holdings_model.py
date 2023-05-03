from datetime import datetime
from decimal import Decimal

from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QBrush, QFont
from PySide6.QtWidgets import QHeaderView
from jal.constants import CustomColor, PredefindedAccountType
from jal.db.helpers import localize_decimal
from jal.db.tree_model import AbstractTreeItem, AbstractTreeModel
from jal.db.account import JalAccount
from jal.db.asset import JalAsset
from jal.widgets.delegates import GridLinesDelegate
from jal.widgets.helpers import ts2d

# ----------------------------------------------------------------------------------------------------------------------
class AssetTreeItem(AbstractTreeItem):
    def __init__(self, data=None, parent=None, group=''):
        super().__init__(parent, group)
        if data is None:
            self.data = {
                'currency_id': 0, 'currency': '', 'account_id': 0, 'account': '', 'asset_id': 0,
                'asset_is_currency': False, 'asset': '', 'asset_name': '', 'expiry': 0, 'qty': Decimal('0'),
                'value_i': Decimal('0'), 'quote': Decimal('0'), 'quote_ts': Decimal('0'), 'quote_a': Decimal('0')
            }
        else:
            self.data = data.copy()

# ----------------------------------------------------------------------------------------------------------------------
class HoldingsModel(AbstractTreeModel):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._groups = []
        self._grid_delegate = None
        self._currency = 0
        self._currency_name = ''
        self._date = QDate.currentDate().endOfDay(Qt.UTC).toSecsSinceEpoch()
        self.calculated_names = ['share', 'profit', 'profit_rel', 'value', 'value_a']
        self._columns = [{'name': self.tr("Currency/Account/Asset")},
                         {'name': self.tr("Asset Name")},
                         {'name': self.tr("Qty")},
                         {'name': self.tr("Open")},
                         {'name': self.tr("Last")},
                         {'name': self.tr("Share, %")},
                         {'name': self.tr("P/L, %")},
                         {'name': self.tr("P/L")},
                         {'name': self.tr("Value")},
                         {'name': self.tr("Value, ")}]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        value = super().headerData(section, orientation, role)
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 9:
            value += self._currency_name
        return value

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return self.data_text(item.data, index.column())
        if role == Qt.FontRole:
            return self.data_font(item.data, index.column())
        if role == Qt.BackgroundRole:
            return self.data_background(item.data, index.column(), self._view.isEnabled())
        if role == Qt.ToolTipRole:
            return self.data_tooltip(item.data, index.column())
        if role == Qt.TextAlignmentRole:
            if index.column() < 2:
                return int(Qt.AlignLeft)
            else:
                return int(Qt.AlignRight)
        return None

    def data_text(self, data, column):
        if column == 0:
            if data['level'] == 0:
                return data['currency']
            elif data['level'] == 1:
                return data['account']
            else:
                return data['asset']
        elif column == 1:
            expiry_text = ""
            if data['expiry']:
                expiry_header = self.tr("Exp:")
                expiry_text = f" [{expiry_header} {ts2d(int(data['expiry']))}]"
            return data['asset_name'] + expiry_text
        elif column == 2:
            if data['qty']:
                if data['asset_is_currency']:
                    decimal_places = 2
                else:
                    decimal_places = -data['qty'].as_tuple().exponent
                    decimal_places = max(min(decimal_places, 6), 0)
                return localize_decimal(Decimal(data['qty']), decimal_places)
            else:
                return ''
        elif column == 3:
            if data['qty'] != Decimal('0') and data['value_i'] != Decimal('0'):
                return f"{(data['value_i'] / data['qty']):,.4f}"
            else:
                return ''
        elif column == 4:
            return f"{float(data['quote']):,.4f}" if data['quote'] and float(data['qty']) != 0 else ''
        elif column == 5:
            return f"{data['share']:,.2f}" if data['share'] else '-.--'
        elif column == 6:
            return f"{Decimal('100') * data['profit_rel']:,.2f}" if data['profit_rel'] else ''
        elif column == 7:
            return f"{data['profit']:,.2f}" if data['profit'] else ''
        elif column == 8:
            return f"{data['value']:,.2f}" if data['value'] else ''
        elif column == 9:
            return f"{data['value_a']:,.2f}" if data['value_a'] else '-.--'
        else:
            assert False

    def data_tooltip(self, data, column):
        if column >= 4 and column <= 8:
            quote_date = datetime.utcfromtimestamp(int(data['quote_ts']))
            quote_age = int((datetime.utcnow() - quote_date).total_seconds() / 86400)
            if quote_age > 7:
                return self.tr("Last quote date: ") + ts2d(int(data['quote_ts']))
        return ''

    def data_font(self, data, column):
        if data['level'] < 2:
            font = QFont()
            font.setBold(True)
            return font
        else:
            if column == 1 and data['expiry']:
                expiry_date = datetime.utcfromtimestamp(int(data['expiry']))
                days_remaining = int((expiry_date - datetime.utcnow()).total_seconds() / 86400)
                if days_remaining <= 10:
                    font = QFont()
                    if days_remaining < 0:
                        font.setStrikeOut(True)
                    else:
                        font.setItalic(True)
                    return font
            if column >= 4 and column <= 8:
                quote_date = datetime.utcfromtimestamp(int(data['quote_ts']))
                quote_age = int((datetime.utcnow()- quote_date).total_seconds() / 86400)
                if quote_age > 7:
                    font = QFont()
                    font.setItalic(True)
                    return font

    def data_background(self, data, column, enabled=True):
        factor = 100 if enabled else 125
        if data['level'] == 0:
            return QBrush(CustomColor.LightPurple.lighter(factor))
        if data['level'] == 1:
            return QBrush(CustomColor.LightBlue.lighter(factor))
        if column == 6 and data['profit_rel']:
            if data['profit_rel'] >= 0:
                return QBrush(CustomColor.LightGreen.lighter(factor))
            else:
                return QBrush(CustomColor.LightRed.lighter(factor))
        if column == 7 and data['profit']:
            if data['profit'] >= 0:
                return QBrush(CustomColor.LightGreen.lighter(factor))
            else:
                return QBrush(CustomColor.LightRed.lighter(factor))

    def configureView(self):
        self._view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._view.header().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(len(self._columns))[2:]:
            self._view.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._grid_delegate = GridLinesDelegate(self._view)
        for i in range(len(self._columns)):
            self._view.setItemDelegateForColumn(i, self._grid_delegate)
        font = self._view.header().font()
        font.setBold(True)
        self._view.header().setFont(font)

    @Slot()
    def setCurrency(self, currency_id):
        if self._currency != currency_id:
            self._currency = currency_id
            self._currency_name = JalAsset(currency_id).symbol()
            self.prepareData()

    @Slot()
    def setDate(self, new_date):
        if self._date != new_date.endOfDay(Qt.UTC).toSecsSinceEpoch():
            self._date = new_date.endOfDay(Qt.UTC).toSecsSinceEpoch()
            self.prepareData()

    def get_data_for_tax(self, index):
        if not index.isValid():
            return None
        item = index.internalPointer()
        return item.data['account_id'], item.data['asset_id'], item.data['currency_id'], item.data['qty']

    def update(self):
        self.prepareData()

    # Populate table 'holdings' with data calculated for given parameters of model: _currency, _date,
    def prepareData(self):
        holdings = []
        accounts = JalAccount.get_all_accounts(account_type=PredefindedAccountType.Investment)
        for account in accounts:
            account_holdings = []
            assets = account.assets_list(self._date)
            rate = JalAsset(account.currency()).quote(self._date, self._currency)[1]
            for asset_data in assets:
                asset = asset_data['asset']
                quote_ts, quote = asset.quote(self._date, account.currency())
                record = {
                    "currency_id": account.currency(),
                    "currency": JalAsset(account.currency()).symbol(),
                    "account_id": account.id(),
                    "account": account.name(),
                    "asset_id": asset.id(),
                    "asset_is_currency": False,
                    "asset": asset.symbol(currency=account.currency()),
                    "asset_name": asset.name(),
                    "expiry": asset.expiry(),
                    "qty": asset_data['amount'],
                    "value_i": asset_data['value'],
                    "quote": quote,
                    "quote_ts": quote_ts,
                    "quote_a": rate * quote
                }
                account_holdings.append(record)
            money = account.get_asset_amount(self._date, account.currency())
            if money:
                account_holdings.append({
                    "currency_id": account.currency(),
                    "currency": JalAsset(account.currency()).symbol(),
                    "account_id": account.id(),
                    "account": account.name(),
                    "asset_id": account.currency(),
                    "asset_is_currency": True,
                    "asset": JalAsset(account.currency()).symbol(),
                    "asset_name": JalAsset(account.currency()).name(),
                    "expiry": 0,
                    "qty": money,
                    "value_i": Decimal('0'),
                    "quote": Decimal('1'),
                    "quote_ts": QDate.currentDate().endOfDay(Qt.UTC).toSecsSinceEpoch(),
                    "quote_a": rate
                })
            account_total = sum(x['qty'] * x['quote'] for x in account_holdings)
            for record in account_holdings:
                record['total'] = account_total
            holdings += account_holdings
        holdings = sorted(holdings, key=lambda x: (x['currency'], x['account'], x['asset_is_currency'], x['asset']))

        self._root = AssetTreeItem()
        currency = 0
        c_node = None
        account = 0
        a_node = None
        for values in holdings:
            values['level'] = 2
            if values['currency_id'] != currency:
                currency = values['currency_id']
                c_node = AssetTreeItem(values, self._root)
                c_node.data['level'] = 0
                c_node.data['asset_name'] = ''
                c_node.data['expiry'] = 0
                c_node.data['qty'] = Decimal('0')
                self._root.appendChild(c_node)
            if values['account_id'] != account:
                account = values['account_id']
                a_node = AssetTreeItem(values, c_node)
                a_node.data['level'] = 1
                a_node.data['asset_name'] = ''
                a_node.data['expiry'] = 0
                a_node.data['qty'] = Decimal('0')
                c_node.appendChild(a_node)
            if values['quote']:
                if values['asset_is_currency']:
                    profit = Decimal('0')
                else:
                    profit = values['quote'] * values['qty'] - values['value_i']
                if values['value_i'] != Decimal('0'):
                    profit_relative = values['quote'] * values['qty'] / values['value_i'] - 1
                else:
                    profit_relative = Decimal('0')
                value = values['quote'] * values['qty']
                share = Decimal('100.0') * value / values['total']
                value_adjusted = values['quote_a'] * values['qty'] if values['quote_a'] else Decimal('0')
                values.update(dict(zip(self.calculated_names, [share, profit, profit_relative, value, value_adjusted])))
            else:
                values.update(dict(zip(self.calculated_names,
                                       [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')])))
            node = AssetTreeItem(values, a_node)
            a_node.appendChild(node)

        # Update totals
        for i in range(self._root.childrenCount()):          # Iterate through each currency
            currency_child = self._root.getChild(i)
            for j in range(currency_child.childrenCount()):  # Iterate through each account for given currency
                self.add_node_totals(currency_child.getChild(j))
            self.add_node_totals(currency_child)
            for j in range(currency_child.childrenCount()):  # Calculate share of each account within currency
                if currency_child.data['value']:
                    currency_child.getChild(j).data['share'] = \
                        Decimal('100') * currency_child.getChild(j).data['value'] / currency_child.data['value']
        # Get full total of totals for all currencies adjusted to common currency
        total = sum([self._root.getChild(i).data['value_a'] for i in range(self._root.childrenCount())])
        for i in range(self._root.childrenCount()):  # Calculate share of each currency (adjusted to common currency)
            if total != Decimal('0'):
                self._root.getChild(i).data['share'] = Decimal('100') * self._root.getChild(i).data['value_a'] / total
            else:
                self._root.getChild(i).data['share'] = None
        self.modelReset.emit()
        self.configureView()
        self._view.expandAll()

    # Update node totals with sum of profit, value and adjusted profit and value of all children
    def add_node_totals(self, node):
        profit = sum([node.getChild(i).data['profit'] for i in range(node.childrenCount())])
        value = sum([node.getChild(i).data['value'] for i in range(node.childrenCount())])
        value_adjusted = sum([node.getChild(i).data['value_a'] for i in range(node.childrenCount())])
        profit_relative = profit / (value - profit) if value != profit else 0
        node.data.update(dict(zip(self.calculated_names, [Decimal('0'), profit, profit_relative, value, value_adjusted])))
