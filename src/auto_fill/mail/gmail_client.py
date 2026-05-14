"""Gmail API client — OAuth2 PKCE flow + message listing.

Setup (1 lan dau):
    python -m auto_fill gmail-setup

Sau khi chay xong, token.json duoc luu tai duong dan trong settings.
Lan sau se tu dong refresh.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Guard: import google libs lazily to avoid ImportError on machines
# where google-api-python-client is not installed.
_GOOGLE_AVAILABLE = False
try:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build as google_build

    _GOOGLE_AVAILABLE = True
except ImportError:
    pass

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailClientError(RuntimeError):
    pass


class GmailClient:
    """Thin wrapper quanh Gmail API v1.

    Parameters
    ----------
    credentials_file:
        Duong dan toi file credentials.json tai ve tu Google Cloud Console.
    token_file:
        Noi luu refresh token sau OAuth flow. Neu khong co, se kich hoat browser.
    """

    def __init__(self, credentials_file: str | Path, token_file: str | Path) -> None:
        if not _GOOGLE_AVAILABLE:
            raise GmailClientError(
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
                    raise GmailClientError(
                        f"Khong tim thay credentials.json tai: {self._creds_file}\n"
                        "Tai ve tu: Google Cloud Console → APIs & Services → Credentials"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(self._creds_file), _SCOPES)
                creds = flow.run_local_server(port=0)

            # Luu token cho lan tiep theo
            self._token_file.parent.mkdir(parents=True, exist_ok=True)
            self._token_file.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def connect(self) -> None:
        """Khoi tao ket noi Gmail API."""
        creds = self._get_credentials()
        self._service = google_build("gmail", "v1", credentials=creds)

    def _ensure_connected(self) -> Any:
        if self._service is None:
            self.connect()
        return self._service

    # ------------------------------------------------------------------ #
    # Message listing                                                      #
    # ------------------------------------------------------------------ #

    def list_messages(
        self,
        query: str = "",
        max_results: int = 50,
        label_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Tra ve list message metadata (id, threadId).

        Parameters
        ----------
        query:
            Gmail search query, e.g. ``"from:abc@gmail.com subject:cap don"``
        max_results:
            So luong toi da tra ve.
        label_ids:
            Loc theo label, e.g. ``["INBOX", "UNREAD"]``.
        """
        svc = self._ensure_connected()
        kwargs: dict[str, Any] = {"userId": "me", "maxResults": max_results}
        if query:
            kwargs["q"] = query
        if label_ids:
            kwargs["labelIds"] = label_ids

        result = svc.users().messages().list(**kwargs).execute()
        messages: list[dict[str, Any]] = result.get("messages", [])
        return messages

    def get_message(self, message_id: str, fmt: str = "full") -> dict[str, Any]:
        """Lay day du thong tin 1 message."""
        svc = self._ensure_connected()
        result: dict[str, Any] = (
            svc.users().messages().get(userId="me", id=message_id, format=fmt).execute()
        )
        return result

    def get_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Tai noi dung 1 attachment theo attachment_id."""
        import base64

        svc = self._ensure_connected()
        att = (
            svc.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = att.get("data", "")
        return base64.urlsafe_b64decode(data + "==")

    def modify_labels(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> None:
        """Them/xoa label cho 1 message."""
        svc = self._ensure_connected()
        body: dict[str, Any] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels
        svc.users().messages().modify(userId="me", id=message_id, body=body).execute()

    def get_or_create_label(self, name: str) -> str:
        """Tra ve labelId; neu chua co thi tao moi."""
        svc = self._ensure_connected()
        labels_resp = svc.users().labels().list(userId="me").execute()
        for lbl in labels_resp.get("labels", []):
            if lbl["name"] == name:
                return str(lbl["id"])
        new_label: dict[str, Any] = (
            svc.users()
            .labels()
            .create(userId="me", body={"name": name, "labelListVisibility": "labelShow"})
            .execute()
        )
        return str(new_label["id"])
