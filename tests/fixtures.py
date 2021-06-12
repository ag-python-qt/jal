import pytest
import os
import json
from shutil import copyfile
from PySide2.QtSql import QSqlDatabase

from constants import Setup
from jal.db.helpers import init_and_check_db, LedgerInitError
from jal.db.update import JalDB
from jal.db.helpers import executeSQL


@pytest.fixture
def project_root() -> str:
    yield os.path.dirname(os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture
def data_path(project_root) -> str:
    yield project_root + os.sep + "tests" + os.sep + "test_data" + os.sep


@pytest.fixture
def prepare_db(project_root, tmp_path, data_path):
    # Prepare environment
    src_path = project_root + os.sep + 'jal' + os.sep + Setup.INIT_SCRIPT_PATH
    target_path = str(tmp_path) + os.sep + Setup.INIT_SCRIPT_PATH
    copyfile(src_path, target_path)

    # Activate db connection
    error = init_and_check_db(str(tmp_path) + os.sep)
    assert error.code == LedgerInitError.EmptyDbInitialized
    error = init_and_check_db(str(tmp_path) + os.sep)
    assert error.code == LedgerInitError.DbInitSuccess
    db = QSqlDatabase.database(Setup.DB_CONNECTION)
    assert db.isValid()
    lang_id = JalDB().get_language_id('en')
    assert lang_id == 1
    yield


@pytest.fixture
def prepare_db_ibkr(prepare_db):
    assert executeSQL("INSERT INTO agents (pid, name) VALUES (0, 'Test Peer')") is not None
    assert executeSQL("INSERT INTO accounts (type_id, name, currency_id, active, number, organization_id) "
                      "VALUES (4, 'Inv. Account', 2, 1, 'U7654321', 1)") is not None
    assert executeSQL("INSERT INTO assets (id, name, type_id, full_name, src_id) "
                      "VALUES (4, 'VUG', 4, 'Growth ETF', 0), "
                      "(5, 'EDV', 4, 'VANGUARD EXTENDED DUR TREAS', 0)") is not None
    assert executeSQL("INSERT INTO dividends (id, timestamp, type, account_id, asset_id, amount, tax, note) "
                      "VALUES (1, 1529612400, 1, 1, 5, 16.76, 1.68, "
                      "'EDV (US9219107094) CASH DIVIDEND USD 0.8381 (Ordinary Dividend)'), "
                      "(2, 1533673200, 1, 1, 5, 20.35, 2.04, "
                      "'EDV(US9219107094) CASH DIVIDEND 0.10175000 USD PER SHARE (Ordinary Dividend)')") is not None

    yield

    # TODO Add fixture cleanup code


# ----------------------------------------------------------------------------------------------------------------------
# provide a json dictionary structure for XLS reports load verification
@pytest.fixture
def test_xls_json(data_path):
    with open(data_path + 'xls.json', 'r') as json_file:
        yield json.load(json_file)
