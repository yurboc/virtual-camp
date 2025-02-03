import datetime
import json
import logging
import apiclient.discovery
from dateutil import parser
from google.oauth2.service_account import Credentials
from typing import Optional, Tuple, List
from utils.config import config
from const.formats import date_h_m_s_fmt

logger = logging.getLogger(__name__)


class GoogleApi:
    def __init__(self) -> None:
        self.spreadsheetId: Optional[str] = None
        self.spreadsheetRange: Optional[str] = None
        self.rawData: Optional[dict] = None

    # Authenticate to Google
    def auth(self) -> None:
        # Read credentials from file
        logger.info("Authenticating to Google...")
        credentials = Credentials.from_service_account_info(
            config["GOOGLE"]["CRED"],
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

    # Set spreadsheet ID
    def setSpreadsheetId(self, spreadsheetId: str) -> None:
        self.spreadsheetId = spreadsheetId

    # Set spreadsheet range
    def setSpreadsheetRange(self, spreadsheetRange: str) -> None:
        self.spreadsheetRange = spreadsheetRange

    # Read spreadsheet data
    def readSpreadsheet(self) -> None:
        logger.info(f"Reading table {self.spreadsheetId}...")
        self.rawData = (
            self.service_sheets.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheetId, range=self.spreadsheetRange)
            .execute()
        )
        logger.info(f"Done reading table {self.spreadsheetId}")

    # Parse spreadsheet data
    def parseSpreadsheet(self, fields: list[str]) -> None:
        logger.info("Parsing data...")
        self.combinedData = list()
        # Iterate over rows
        if not self.rawData:
            return
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

    # Save spreadsheet data to JS file
    def saveSpreadsheetToJs(self, filename: str) -> None:
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

    # Prepare folder for VirtualCamp sheets
    def prepareFolder(self) -> str:
        folder_name = config["GOOGLE"]["DRIVE"]["ABONEMENT_FOLDER"]
        logger.info("Preparing folder %s...", folder_name)
        # Check if folder exists
        query = (
            f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        )
        results = (
            self.service_drive.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id)",
            )
            .execute()
        )
        folders = results.get("files", [])
        if folders:
            self.currentFolder = folders[0]["id"]
            logger.info(f"Folder found, ID: {self.currentFolder}")
            return self.currentFolder
        # Create folder
        folder = (
            self.service_drive.files()
            .create(
                body={
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                },
                fields="id",
            )
            .execute()
        )
        self.currentFolder = folder.get("id")
        logger.info(f"Folder created, ID: {self.currentFolder}")
        return self.currentFolder

    # Create spreadsheet from template
    def createFromTemplate(self, name) -> Optional[str]:
        template = config["GOOGLE"]["DRIVE"]["ABONEMENT_TEMPLATE"]
        logger.info("Creating table %s from template %s", name, template)
        copy_body = {"name": name}
        copy_body["parents"] = [self.currentFolder]
        copied_file = (
            self.service_drive.files().copy(fileId=template, body=copy_body).execute()
        )
        new_sheet_id = copied_file.get("id")
        self.spreadsheetId = new_sheet_id
        logger.info("Done creating table: %s", self.spreadsheetId)
        return self.spreadsheetId

    # Set access to spreadsheet
    def setAccess(
        self, role: str = "commenter", emailAddress: Optional[str] = None
    ) -> None:
        logger.info("Setting access %s to %s", role, self.spreadsheetId)
        # Select role
        if emailAddress:
            body = {"role": role, "type": "user", "emailAddress": emailAddress}
        else:
            body = {"role": role, "type": "anyone"}
        # Set access
        self.service_drive.permissions().create(
            fileId=self.spreadsheetId,
            body=body,
            fields="id",
        ).execute()
        logger.info("Done setting access")

    # Get link to spreadsheet
    def getLink(self) -> str:
        return config["GOOGLE"]["DRIVE"]["LINK_TEMPLATE"].format(self.spreadsheetId)

    # Delete file
    def deleteFile(self, spreadsheetId: Optional[str] = None) -> None:
        if not spreadsheetId:
            spreadsheetId = self.spreadsheetId
        logger.info("Deleting file %s", spreadsheetId)
        self.service_drive.files().delete(fileId=spreadsheetId).execute()
        logger.info("Done deleting file")

    # List Files and Folders
    def listItems(self) -> None:
        results = (
            self.service_drive.files()
            .list(fields="files(id, name, parents, mimeType)")
            .execute()
        )
        folder_cache = {}
        items = results.get("files", [])
        if not items:
            logger.info("No files found.")
        else:
            logger.info("Files:")
            for item in items:
                file_name = item.get("name")
                file_id = item.get("id")
                mime_type = item["mimeType"]
                item_type = mime_type.split("/")[-1].split(".")[-1]
                if "parents" in item:
                    parent_id = item["parents"][0]
                    if parent_id not in folder_cache:
                        parent_folder = (
                            self.service_drive.files()
                            .get(fileId=parent_id, fields="name")
                            .execute()
                        )
                        folder_cache[parent_id] = parent_folder.get(
                            "name", "Unknown folder"
                        )
                    folder_name = folder_cache[parent_id]
                else:
                    folder_name = "Root"
                logger.info(
                    "{0}: {1}: {2} ({3})".format(
                        folder_name, item_type, file_name, file_id
                    )
                )

    # Fill Abonement Info
    def abonementUpdate(
        self,
        abonement_name: Optional[str],
        token: Optional[str],
        expiry_date: Optional[str],
        total_visits: Optional[int | str],
        description: Optional[str],
        owner_name: Optional[str],
    ) -> None:
        # Update fields
        self.service_sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheetId,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": config["GOOGLE"]["DRIVE"]["ABONEMENT_INFO_RANGE"],
                        "majorDimension": "ROWS",
                        "values": [
                            [abonement_name if abonement_name else ""],
                            [description if description else ""],
                            [None, token if token else ""],
                            [None, expiry_date if expiry_date else ""],
                            [None, total_visits if total_visits else ""],
                            [None, owner_name if owner_name else ""],
                        ],
                    }
                ],
            },
        ).execute()
        logger.info("Done updating table")
        # Rename file
        self.service_drive.files().update(
            fileId=self.spreadsheetId, body={"name": abonement_name or "wrong_name"}
        ).execute()
        logger.info("Done rename file")

    # Add Visit to Abonement
    def visitAdd(self, visit_id: int, date: str, user_name: str) -> None:
        logger.info("Add Visit to Abonement...")
        # Update fields
        self.service_sheets.spreadsheets().values().append(
            spreadsheetId=self.spreadsheetId,
            insertDataOption="OVERWRITE",
            valueInputOption="USER_ENTERED",
            range=config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_START"],
            body={"values": [[date, user_name, visit_id, "1"]]},
        ).execute()
        logger.info("Done updating table")

    # Visit Update
    def visitUpdate(self, visit_id: int, visit_new_ts: str) -> None:
        logger.info("Update Visit in Abonement...")

        # Find current Visit
        res = self.findVisitById(visit_id)
        if not res:
            logger.info("Visit not found")
            return
        row_id, row = res

        # Update edited Visit
        row[0] = visit_new_ts
        self.updateRowValues(
            config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_ROW"].format(
                row_id + 1, row_id + 1
            ),
            [row],
        )

        # Update row color
        self.updateRowColor([row_id, row_id + 1], [0, 4], [1.0, 1.0, 0.7])
        logger.info("Done update Visit in Abonement")

    # Visit Delete
    def visitDelete(self, visit_id: int) -> None:
        logger.info("Update Visit in Abonement...")

        # Find current Visit
        res = self.findVisitById(visit_id)
        if not res:
            logger.info("Visit not found")
            return
        row_id, row = res

        # Update deleted Visit
        row[3] = "0"
        self.updateRowValues(
            config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_ROW"].format(
                row_id + 1, row_id + 1
            ),
            [row],
        )

        # Update row color
        self.updateRowColor([row_id, row_id + 1], [0, 4], [1.0, 0.7, 0.7])
        logger.info("Done update Visit in Abonement")

    # Find Visit Row by ID
    def findVisitById(self, visit_id: int) -> Optional[Tuple[int, List[str]]]:
        results = (
            self.service_sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.spreadsheetId,
                range=config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_RANGE"],
            )
            .execute()
        )
        current_visits = results.get("values", [])
        found_row = None
        for row in current_visits:
            if row[2] == str(visit_id):
                found_row_id = current_visits.index(row)
                found_row = current_visits[found_row_id]
                logger.info("Found row %s", found_row_id)
                break
        if not found_row:
            logger.info("Row not found")
            return None
        else:
            found_row_id += 1  # Skip header
        return found_row_id, found_row

    # Update Row Values
    def updateRowValues(self, range: str, values: List[List[str]]) -> None:
        self.service_sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheetId,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [{"range": range, "majorDimension": "ROWS", "values": values}],
            },
        ).execute()

    # Update Row Color
    def updateRowColor(
        self, row: List[int], col: List[int], color: List[float]
    ) -> None:
        self.service_sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheetId,
            body={
                "requests": [
                    {
                        "repeatCell": {
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {
                                        "red": color[0],
                                        "green": color[1],
                                        "blue": color[2],
                                        "alpha": 1,
                                    }
                                }
                            },
                            "range": {
                                "sheetId": 0,
                                "startRowIndex": row[0],
                                "endRowIndex": row[1],
                                "startColumnIndex": col[0],
                                "endColumnIndex": col[1],
                            },
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    }
                ]
            },
        ).execute()

    # Update Visits for Abonement
    def visitsUpdateAll(self, visits: List[Tuple[int, str, str]]) -> None:
        logger.info("Sync Visits for Abonement...")
        # Get current Visits
        results = (
            self.service_sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.spreadsheetId,
                range=config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_RANGE"],
            )
            .execute()
        )
        current_visits = results.get("values", [])
        found_visits = []
        for row in current_visits:
            found_visits.append(row[2])

        # Take unique Vsits
        new_visits = []
        for visit in visits:
            visit_id, visit_ts, visit_user = visit
            if str(visit_id) in found_visits:
                continue
            new_visits.append([visit_ts, visit_user, visit_id, "1"])

        # Add new Visits
        logger.info("Found %d new Visits...", len(new_visits))
        self.service_sheets.spreadsheets().values().append(
            spreadsheetId=self.spreadsheetId,
            insertDataOption="OVERWRITE",
            valueInputOption="USER_ENTERED",
            range=config["GOOGLE"]["DRIVE"]["ABONEMENT_VISIT_START"],
            body={"values": new_visits},
        ).execute()
        logger.info("Done Sync Visits")
