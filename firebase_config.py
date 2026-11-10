"""
FeedbackTrack - Firestore access WITHOUT any admin key.

This module replaces the old firebase_admin based version. It talks to the
Firestore REST API using the signed-in user's own Firebase ID token, so every
request is checked by your Firestore Security Rules (see firestore.rules).
Nothing secret is stored in this application.

Public API (kept compatible with the old code):
    db.collection("x").document("id").get() / set() / update() / delete()
    db.collection("x").where(field, op, value).limit(n).get() / stream()
    db.collection("x").add({...})

Session helpers (used by the login / signup / account pages):
    set_session(auth_result)   store the tokens returned by Firebase Auth
    clear_session()
    current_uid()

The session lives in environment variables so that pages opened as child
processes automatically inherit the signed-in user.
"""

import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

# These two values are NOT secrets. The Web API key only identifies your
# Firebase project; Security Rules decide what each user may do.
PROJECT_ID = "taskmanagerapp-35a3d"
FIREBASE_API_KEY = "AIzaSyBd1KHyHiU9OfPu1BoH3H3KORtUJrOZbmg"

FIRESTORE_ROOT = (
    f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}"
    "/databases/(default)/documents"
)
TOKEN_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

_TIMEOUT = 20
_ENV_ID = "FT_ID_TOKEN"
_ENV_REFRESH = "FT_REFRESH_TOKEN"
_ENV_EXPIRES = "FT_TOKEN_EXPIRES_AT"
_ENV_UID = "FT_UID"

_http = requests.Session()


# ============================================================
# ERRORS
# ============================================================
class FirestoreError(Exception):
    def __init__(self, status, message):
        super().__init__(f"Firestore error {status}: {message}")
        self.status = status
        self.message = message


class PermissionDenied(FirestoreError):
    pass


# ============================================================
# SESSION (signed-in user)
# ============================================================
def set_session(auth_result):
    """Store the tokens from a signIn / signUp / accounts:update response."""
    if not auth_result or not auth_result.get("idToken"):
        return
    os.environ[_ENV_ID] = auth_result["idToken"]
    if auth_result.get("refreshToken"):
        os.environ[_ENV_REFRESH] = auth_result["refreshToken"]
    expires_in = int(auth_result.get("expiresIn", 3600) or 3600)
    os.environ[_ENV_EXPIRES] = str(time.time() + expires_in)
    uid = auth_result.get("localId") or auth_result.get("user_id")
    if uid:
        os.environ[_ENV_UID] = uid


def clear_session():
    for name in (_ENV_ID, _ENV_REFRESH, _ENV_EXPIRES, _ENV_UID):
        os.environ.pop(name, None)


def current_uid():
    return os.environ.get(_ENV_UID) or None


def _refresh_token():
    refresh = os.environ.get(_ENV_REFRESH)
    if not refresh:
        return False
    try:
        response = _http.post(
            TOKEN_REFRESH_URL,
            params={"key": FIREBASE_API_KEY},
            data={"grant_type": "refresh_token", "refresh_token": refresh},
            timeout=_TIMEOUT,
        )
        if not response.ok:
            return False
        data = response.json()
        set_session({
            "idToken": data.get("id_token"),
            "refreshToken": data.get("refresh_token"),
            "expiresIn": data.get("expires_in", 3600),
            "localId": data.get("user_id"),
        })
        return True
    except (requests.RequestException, ValueError):
        return False


def _id_token():
    token = os.environ.get(_ENV_ID)
    if not token:
        return None
    try:
        expires_at = float(os.environ.get(_ENV_EXPIRES, "0"))
    except ValueError:
        expires_at = 0
    if time.time() > expires_at - 60:
        _refresh_token()
        token = os.environ.get(_ENV_ID)
    return token


def _request(method, url, **kwargs):
    for attempt in (1, 2):
        headers = kwargs.pop("headers", {}) or {}
        token = _id_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = _http.request(
            method, url, headers=headers, timeout=_TIMEOUT, **kwargs
        )
        if response.status_code == 401 and token and attempt == 1:
            if _refresh_token():
                continue
        return response
    return response


def _raise_for(response):
    if response.ok:
        return
    try:
        message = response.json().get("error", {}).get("message", "")
    except ValueError:
        message = response.text[:200]
    if response.status_code in (401, 403):
        raise PermissionDenied(response.status_code, message)
    raise FirestoreError(response.status_code, message)


# ============================================================
# VALUE CONVERSION (Python <-> Firestore REST JSON)
# ============================================================
def _encode(value):
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, datetime):
        # Same rule as the Firestore SDK: naive datetimes are treated as UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return {"timestampValue": value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
    if isinstance(value, (list, tuple)):
        return {"arrayValue": {"values": [_encode(v) for v in value]}}
    if isinstance(value, dict):
        return {"mapValue": {"fields": {str(k): _encode(v) for k, v in value.items()}}}
    raise TypeError(f"Unsupported Firestore value type: {type(value).__name__}")


_TS_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?Z$"
)


def _parse_timestamp(text):
    match = _TS_RE.match(text)
    if not match:
        return text
    year, month, day, hour, minute, second, fraction = match.groups()
    micro = int((fraction or "0").ljust(6, "0")[:6])
    return datetime(
        int(year), int(month), int(day),
        int(hour), int(minute), int(second), micro,
        tzinfo=timezone.utc,
    )


def _decode(value):
    if "stringValue" in value:
        return value["stringValue"]
    if "integerValue" in value:
        return int(value["integerValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "booleanValue" in value:
        return value["booleanValue"]
    if "timestampValue" in value:
        return _parse_timestamp(value["timestampValue"])
    if "mapValue" in value:
        return _decode_fields(value["mapValue"].get("fields", {}))
    if "arrayValue" in value:
        return [_decode(v) for v in value["arrayValue"].get("values", [])]
    if "referenceValue" in value:
        return value["referenceValue"]
    if "geoPointValue" in value:
        return value["geoPointValue"]
    return None  # nullValue and anything unknown


def _decode_fields(fields):
    return {key: _decode(val) for key, val in (fields or {}).items()}


_SIMPLE_FIELD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _field_path(path):
    parts = path.split(".")
    return ".".join(
        p if _SIMPLE_FIELD.match(p) else "`" + p.replace("`", "\\`") + "`"
        for p in parts
    )


def _nest(path, encoded):
    """Turn 'a.b' + value into {'a': {'mapValue': {'fields': {'b': value}}}}."""
    parts = path.split(".")
    result = encoded
    for part in reversed(parts[1:]):
        result = {"mapValue": {"fields": {part: result}}}
    return parts[0], result


def _merge_fields(target, key, encoded):
    if (
        key in target
        and "mapValue" in target[key]
        and "mapValue" in encoded
    ):
        inner = target[key]["mapValue"].setdefault("fields", {})
        for k, v in encoded["mapValue"].get("fields", {}).items():
            _merge_fields(inner, k, v)
    else:
        target[key] = encoded


# ============================================================
# SNAPSHOTS AND REFERENCES
# ============================================================
class DocumentSnapshot:
    def __init__(self, reference, data, exists=True):
        self.reference = reference
        self.id = reference.id
        self.exists = exists
        self._data = data

    def to_dict(self):
        return dict(self._data) if self.exists and self._data is not None else None

    def get(self, field):
        return (self._data or {}).get(field)


class DocumentReference:
    def __init__(self, path):
        self.path = path.strip("/")
        self.id = self.path.split("/")[-1]

    def _url(self):
        encoded = "/".join(quote(p, safe="") for p in self.path.split("/"))
        return f"{FIRESTORE_ROOT}/{encoded}"

    def get(self):
        response = _request("GET", self._url())
        if response.status_code == 404:
            return DocumentSnapshot(self, None, exists=False)
        _raise_for(response)
        return DocumentSnapshot(
            self, _decode_fields(response.json().get("fields", {}))
        )

    def set(self, data, merge=False):
        fields = {str(k): _encode(v) for k, v in data.items()}
        params = []
        if merge:
            params = [("updateMask.fieldPaths", _field_path(k)) for k in data]
        response = _request(
            "PATCH", self._url(), params=params, json={"fields": fields}
        )
        _raise_for(response)

    def update(self, data):
        fields = {}
        params = [("currentDocument.exists", "true")]
        for path, value in data.items():
            params.append(("updateMask.fieldPaths", _field_path(path)))
            key, encoded = _nest(path, _encode(value))
            _merge_fields(fields, key, encoded)
        response = _request(
            "PATCH", self._url(), params=params, json={"fields": fields}
        )
        _raise_for(response)

    def delete(self):
        _raise_for(_request("DELETE", self._url()))

    def collection(self, name):
        return CollectionReference(f"{self.path}/{name}")


_OPERATORS = {
    "==": "EQUAL",
    "!=": "NOT_EQUAL",
    "<": "LESS_THAN",
    "<=": "LESS_THAN_OR_EQUAL",
    ">": "GREATER_THAN",
    ">=": "GREATER_THAN_OR_EQUAL",
    "array_contains": "ARRAY_CONTAINS",
    "in": "IN",
    "not-in": "NOT_IN",
    "array_contains_any": "ARRAY_CONTAINS_ANY",
}


class Query:
    DESCENDING = "DESCENDING"
    ASCENDING = "ASCENDING"

    def __init__(self, collection_path, filters=None, limit=None, order=None):
        self._path = collection_path.strip("/")
        self._filters = list(filters or [])
        self._limit = limit
        self._order = list(order or [])

    def _clone(self, **changes):
        state = {
            "filters": self._filters,
            "limit": self._limit,
            "order": self._order,
        }
        state.update(changes)
        return Query(self._path, **state)

    def where(self, field, op, value):
        if op not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {op}")
        return self._clone(filters=self._filters + [(field, _OPERATORS[op], value)])

    def limit(self, count):
        return self._clone(limit=int(count))

    def order_by(self, field, direction="ASCENDING"):
        direction = "DESCENDING" if str(direction).upper().startswith("DESC") else "ASCENDING"
        return self._clone(order=self._order + [(field, direction)])

    def _structured_query(self):
        parent_parts = self._path.split("/")
        query = {"from": [{"collectionId": parent_parts[-1]}]}
        filters = [
            {
                "fieldFilter": {
                    "field": {"fieldPath": _field_path(f)},
                    "op": op,
                    "value": _encode(v),
                }
            }
            for f, op, v in self._filters
        ]
        if len(filters) == 1:
            query["where"] = filters[0]
        elif filters:
            query["where"] = {
                "compositeFilter": {"op": "AND", "filters": filters}
            }
        if self._order:
            query["orderBy"] = [
                {"field": {"fieldPath": _field_path(f)}, "direction": d}
                for f, d in self._order
            ]
        if self._limit is not None:
            query["limit"] = self._limit
        return query

    def _run_url(self):
        parent_parts = self._path.split("/")[:-1]
        if not parent_parts:
            return f"{FIRESTORE_ROOT}:runQuery"
        encoded = "/".join(quote(p, safe="") for p in parent_parts)
        return f"{FIRESTORE_ROOT}/{encoded}:runQuery"

    def get(self):
        response = _request(
            "POST", self._run_url(),
            json={"structuredQuery": self._structured_query()},
        )
        _raise_for(response)
        results = []
        for row in response.json():
            document = row.get("document")
            if not document:
                continue
            relative = document["name"].split("/documents/", 1)[1]
            results.append(
                DocumentSnapshot(
                    DocumentReference(relative),
                    _decode_fields(document.get("fields", {})),
                )
            )
        return results

    def stream(self):
        return iter(self.get())


class CollectionReference(Query):
    def __init__(self, path):
        super().__init__(path)

    def document(self, document_id=None):
        if document_id is None:
            import uuid
            document_id = uuid.uuid4().hex[:20]
        return DocumentReference(f"{self._path}/{document_id}")

    def add(self, data):
        fields = {str(k): _encode(v) for k, v in data.items()}
        parent_parts = self._path.split("/")
        url = f"{FIRESTORE_ROOT}/" + "/".join(quote(p, safe="") for p in parent_parts)
        response = _request("POST", url, json={"fields": fields})
        _raise_for(response)
        relative = response.json()["name"].split("/documents/", 1)[1]
        return datetime.now(timezone.utc), DocumentReference(relative)


class Client:
    def collection(self, name):
        return CollectionReference(name)

    def document(self, path):
        return DocumentReference(path)


db = Client()


def delete_auth_account(id_token):
    """Undo a half-finished signup (Auth account created, profile rejected)."""
    try:
        _http.post(
            "https://identitytoolkit.googleapis.com/v1/accounts:delete",
            params={"key": FIREBASE_API_KEY},
            json={"idToken": id_token},
            timeout=_TIMEOUT,
        )
    except requests.RequestException:
        pass


# ============================================================
# USERNAME LOOKUP (from the existing "users" collection)
# ------------------------------------------------------------
# Login happens by username, but at that moment nobody is signed in yet.
# The rules allow a username search that returns at most ONE profile
# (see firestore.rules). No separate collection is needed.
# ============================================================
def lookup_username(username):
    """Return {'uid', 'email', 'role', ...} for a username, or None."""
    matches = (
        db.collection("users")
        .where("username", "==", str(username).strip())
        .limit(1)
        .get()
    )
    if not matches:
        return None
    data = matches[0].to_dict() or {}
    data["uid"] = matches[0].id
    return data