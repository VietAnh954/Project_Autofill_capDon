"""Google Drive API client — download restricted Excel/Sheets files.

Setup (1 lan dau):
    python -m auto_fill drive-setup

Can: credentials.json tu Google Cloud Console (co the dung chung voi Gmail).
Phai enable: Google Drive API trong Cloud Console.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

_GOOGLE_AVAILABLE = False
try:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build as google_build
    from googleapiclient.http import MediaIoBaseDownload

    _GOOGLE_AVAILABLE = True
except ImportError:
    pass

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class DriveClientError(RuntimeError):
    pass


class DriveClient:
    """Thin wrapper around Google Drive API v3.

    Parameters
    ----------
    credentials_file:
        Path toi credentials.json tu Google Cloud Console.
    token_file:
        Noi luu refresh token sau OAuth flow.
    """

    def __init__(self, credentials_file: str | Path, token_file: str | Path) -> None:
        if not _GOOGLE_AVAILABLE:
            raise DriveClientError(
                "google-api-python-client chua duoc cai. "
                "Chay: pip install google-api-python-client google-auth-oauthlib"
            )
        self._creds_file = Path(credentials_file)
        self._token_file = Path(token_file)
        self._service: Any | None = None

    # ------------------------------------------------------------------ #
    # Auth                                                                 #
    # ------------------------------------------------------------------ #

    def _get_credentials(self) -> Any:
        creds: Any = None
        if self._token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_file), _SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                if not self._creds_file.exists():
                    raise DriveClientError(
                        f"Khong tim thay credentials.json tai: {self._creds_file}\n"
                        "Tai ve tu: Google Cloud Console → APIs & Services → Credentials\n"
                        "Bat buoc: Enable 'Google Drive API' trong Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(self._creds_file), _SCOPES)
                creds = flow.run_local_server(port=0)

            self._token_file.parent.mkdir(parents=True, exist_ok=True)
            self._token_file.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def connect(self) -> None:
        """Khoi tao ket noi Drive API."""
        creds = self._get_credentials()
        self._service = google_build("drive", "v3", credentials=creds)

    def _ensure_connected(self) -> Any:
        if self._service is None:
            self.connect()
        return self._service

    # ------------------------------------------------------------------ #
    # Download                                                             #
    # ------------------------------------------------------------------ #

    def download_as_xlsx(self, file_id: str, dest: Path) -> Path:
        """Download Google Sheet hoac xlsx tu Drive ve local.

        Kiem tra mimeType truoc:
        - Google Sheets native → export sang xlsx.
        - File xlsx upload (mimeType khac) → get_media download goc.

        Parameters
        ----------
        file_id:
            ID cua file tren Google Drive (trong URL /d/<FILE_ID>/).
        dest:
            Duong dan luu file local (.xlsx).

        Returns
        -------
        Path toi file da download.
        """
        svc = self._ensure_connected()
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Lay mimeType de quyet dinh cach download
        meta = svc.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime = meta.get("mimeType", "")

        if "google-apps.spreadsheet" in mime:
            # Native Google Sheet → export sang xlsx
            request = svc.files().export_media(fileId=file_id, mimeType=_XLSX_MIME)
        else:
            # File xlsx/xlsm upload len Drive → tai file goc
            request = svc.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        dest.write_bytes(buf.getvalue())
        return dest
