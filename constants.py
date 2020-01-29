DB_PATH = "/home/vtitov/projects/ledger/ledger.sqlite"
CALC_TOLERANCE = 10e-9

# PREDEFINED BOOK ACCOUNTS
BOOK_ACCOUNT_COSTS          = 1
BOOK_ACCOUNT_INCOMES        = 2
BOOK_ACCOUNT_MONEY          = 3
BOOK_ACCOUNT_ACTIVES        = 4
BOOK_ACCOUNT_LIABILITIES    = 5
BOOK_ACCOUNT_TRANSFERS      = 6

# PREDEFINED TRANSACTION TYPES
TRANSACTION_ACTION      = 1
TRANSACTION_DIVIDEND    = 2
TRANSACTION_TRADE       = 3
TRANSACTION_TRANSFER    = 4
# TRANSFER SUB-TYPES
TRANSFER_FEE    = 0
TRANSFER_OUT    = -1
TRANSFER_IN     = 1

# PREDEFINED CATEGORIES
CATEGORY_TRANSFER_IN    = 107
CATEGORY_TRANSFER_OUT   = 108
CATEGORY_FEES           = 109
CATEGORY_TAXES          = 110
CATEGORY_DIVIDEND       = 111
CATEGORY_PROFIT         = 114

# PREDEFINED CURRENCY
CURRENCY_RUBLE = 15
# PREDEFINED TYPE FOR MONEY
ACTIVE_TYPE_MONEY = 1

# PREDEFINED PEERS
PEER_FINANCIAL          = 1

from PySide2.QtGui import QColor
DARK_GREEN_COLOR = QColor(0, 100, 0)
DARK_RED_COLOR = QColor(139, 0, 0)
DARK_BLUE_COLOR = QColor(0, 0, 139)
BLUE_COLOR = QColor(0, 0, 255)
LIGHT_BLUE_COLOR = QColor(150, 200, 255)
LIGHT_PURPLE_COLOR = QColor(200, 150, 255)
LIGHT_GREEN_COLOR = QColor(127, 255, 127)
LIGHT_RED_COLOR = QColor(255, 127, 127)

TAB_ACTION =    0
TAB_DIVIDEND =  2
TAB_TRADE =     1
TAB_TRANSFER =  3