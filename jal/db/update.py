import logging
from datetime import datetime
from jal.constants import Setup
from jal.db.helpers import db_connection, executeSQL, readSQL, get_asset_name
from jal.widgets.helpers import g_tr


# ----------------------------------------------------------------------------------------------------------------------
class JalDB():
    def __init__(self):
        pass

    def commit(self):
        db_connection().commit()

    def update_quote(self, asset_id, timestamp, quote):
        if (timestamp is None) or (quote is None):
            return
        old_id = 0
        query = executeSQL("SELECT id FROM quotes WHERE asset_id = :asset_id AND timestamp = :timestamp",
                           [(":asset_id", asset_id), (":timestamp", timestamp)])
        if query.next():
            old_id = query.value(0)
        if old_id:
            executeSQL("UPDATE quotes SET quote=:quote WHERE id=:old_id", [(":quote", quote), (":old_id", old_id), ])
        else:
            executeSQL("INSERT INTO quotes(timestamp, asset_id, quote) VALUES (:timestamp, :asset_id, :quote)",
                       [(":timestamp", timestamp), (":asset_id", asset_id), (":quote", quote)])
        logging.info(g_tr('JalDB', "Quote loaded: ") +
                     f"{get_asset_name(asset_id)} " 
                     f"@ {datetime.utcfromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')} = {quote}")

    def add_trade(self, account_id, asset_id, timestamp, settlement, number, qty, price, fee):
        trade_id = readSQL("SELECT id FROM trades "
                           "WHERE timestamp=:timestamp AND asset_id = :asset "
                           "AND account_id = :account AND number = :number AND qty = :qty AND price = :price",
                           [(":timestamp", timestamp), (":asset", asset_id), (":account", account_id),
                            (":number", number), (":qty", qty), (":price", price)])
        if trade_id:
            logging.info(g_tr('JalDB', "Trade already exists: #") + f"{number}")
            return

        _ = executeSQL("INSERT INTO trades (timestamp, settlement, number, account_id, asset_id, qty, price, fee) "
                       "VALUES (:timestamp, :settlement, :number, :account, :asset, :qty, :price, :fee)",
                       [(":timestamp", timestamp), (":settlement", settlement), (":number", number),
                        (":account", account_id), (":asset", asset_id), (":qty", float(qty)),
                        (":price", float(price)), (":fee", -float(fee))], commit=True)

    def del_trade(self, account_id, asset_id, timestamp, _settlement, number, qty, price, _fee):
        _ = executeSQL("DELETE FROM trades "
                       "WHERE timestamp=:timestamp AND asset_id=:asset "
                       "AND account_id=:account AND number=:number AND qty=:qty AND price=:price",
                       [(":timestamp", timestamp), (":asset", asset_id), (":account", account_id),
                        (":number", number), (":qty", -qty), (":price", price)], commit=True)

    def add_transfer(self, timestamp, f_acc_id, f_amount, t_acc_id, t_amount, fee_acc_id, fee, note):
        transfer_id = readSQL("SELECT id FROM transfers WHERE withdrawal_timestamp=:timestamp "
                              "AND withdrawal_account=:from_acc_id AND deposit_account=:to_acc_id",
                              [(":timestamp", timestamp), (":from_acc_id", f_acc_id), (":to_acc_id", t_acc_id)])
        if transfer_id:
            logging.info(g_tr('JalDB', "Transfer/Exchange already exists: ") + f"{f_amount}->{t_amount}")
            return
        if abs(fee) > Setup.CALC_TOLERANCE:
            _ = executeSQL("INSERT INTO transfers (withdrawal_timestamp, withdrawal_account, withdrawal, "
                           "deposit_timestamp, deposit_account, deposit, fee_account, fee, note) "
                           "VALUES (:timestamp, :f_acc_id, :f_amount, :timestamp, :t_acc_id, :t_amount, "
                           ":fee_acc_id, :fee_amount, :note)",
                           [(":timestamp", timestamp), (":f_acc_id", f_acc_id), (":t_acc_id", t_acc_id),
                            (":f_amount", f_amount), (":t_amount", t_amount), (":fee_acc_id", fee_acc_id),
                            (":fee_amount", fee), (":note", note)], commit=True)
        else:
            _ = executeSQL("INSERT INTO transfers (withdrawal_timestamp, withdrawal_account, withdrawal, "
                           "deposit_timestamp, deposit_account, deposit, note) "
                           "VALUES (:timestamp, :f_acc_id, :f_amount, :timestamp, :t_acc_id, :t_amount, :note)",
                           [(":timestamp", timestamp), (":f_acc_id", f_acc_id), (":t_acc_id", t_acc_id),
                            (":f_amount", f_amount), (":t_amount", t_amount), (":note", note)], commit=True)