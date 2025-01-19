import datetime
import json
import logging
import apiclient.discovery
from dateutil import parser
from google.oauth2.service_account import Credentials
from utils.config import config
from const.text import date_h_m_s_fmt

logger = logging.getLogger(__name__)


class TableConverter:
    def __init__(self):
        self.spreadsheetId = None
        self.spreadsheetRange = None
        self.rawData = None

    def auth(self):
        # Read credentials from file
        logger.info("Authenticating to Google...")
        credentials = Credentials.from_service_account_info(
            config["CRED_GOOGLE"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        # Select service modules
        self.service_sheets = apiclient.discovery.build(
            "sheets", "v4", credentials=credentials
        )
        self.service_drive = apiclient.discovery.build(
            "drive", "v3", credentials=credentials
        )
        logger.info("Done authenticating to Google")

    def setSpreadsheetId(self, spreadsheetId):
        self.spreadsheetId = spreadsheetId

    def setSpreadsheetRange(self, spreadsheetRange):
        self.spreadsheetRange = spreadsheetRange

    def readTable(self):
        logger.info(f"Reading table {self.spreadsheetId}...")
        self.rawData = (
            self.service_sheets.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheetId, range=self.spreadsheetRange)
            .execute()
        )
        logger.info(f"Done reading table {self.spreadsheetId}")

    def parseData(self, fields):
        logger.info("Parsing data...")
        self.combinedData = list()
        # Iterate over rows
        for rowData in self.rawData["values"]:
            tmpRow: dict[str, str] = dict()
            # Iterate over columns
            col_id = 0
            for col_name in fields:
                tmpRow[col_name] = rowData[col_id] if col_id < len(rowData) else ""
                col_id += 1
            # Save row
            self.combinedData.append(tmpRow)
        # Get date of last update and generation
        docInfo = (
            self.service_drive.files()
            .get(fileId=self.spreadsheetId, fields="name, modifiedTime")
            .execute()
        )
        self.docName = docInfo.get("name")
        modifiedTime = docInfo.get("modifiedTime")
        modifiedTimeParsed = parser.parse(modifiedTime)
        self.lastUpdateDate = modifiedTimeParsed.strftime(date_h_m_s_fmt)
        self.generationDate = datetime.datetime.now().strftime(date_h_m_s_fmt)
        # Write details to log
        logger.info(f"File name: {self.docName}")
        logger.info(f"Last update: {self.lastUpdateDate}")
        logger.info(f"Generation date: {self.generationDate}")
        logger.info(f"Lines count: {len(self.combinedData)}")

    def saveToFile(self, filename):
        logger.info("Saving to file...")
        with open(filename, "w") as f:
            f.write("var php_data = ")
            f.write(
                json.dumps(self.combinedData, separators=(",", ":"), ensure_ascii=False)
            )
            f.write(";\n")
            f.write(f'var modified_date="{self.lastUpdateDate}";\n')
            f.write(f'var generated_date="{self.generationDate}";\n')
        logger.info(f"Saved to file: {filename}")
