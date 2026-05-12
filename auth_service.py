from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


DB_PATH = Path("planner.db")
DEFAULT_LOCAL_USER_ID = "local_default_user"
DEFAULT_LOCAL_USER_NAME = "本地默认用户"
LOCAL_ACCOUNT_POSITIONS = ("售前", "售后")
ITEM_TYPE_OPTIONS = ("方案交流", "方案汇报", "POC1", "POC2", "交付", "服务", "基建")
PROJECT_TYPE_OPTIONS = ("A", "B+", "B", "C")
SALES_OPTIONS = ("张泽恒", "秦瑞", "王晖", "王鑫泽")
SERVICE_MODE_OPTIONS = ("客户现场", "远程支持")
DEFAULT_LOCAL_ACCOUNT_POSITION = "售后"
LOCAL_ACCOUNT_POSITION_OPTIONS_SETTING_KEY = "local_account_position_options_json"
ITEM_TYPE_OPTIONS_SETTING_KEY = "item_type_options_json"
PROJECT_TYPE_OPTIONS_SETTING_KEY = "project_type_options_json"
SALES_OPTIONS_SETTING_KEY = "sales_options_json"
SERVICE_MODE_OPTIONS_SETTING_KEY = "service_mode_options_json"
DEPARTMENT_OPTIONS_SETTING_KEY = "department_options_json"
POSITION_FIELD_SCOPE_SETTING_KEY = "position_field_scope_json"
SESSION_DURATION_DAYS = 7
ADMIN_PASSWORD_PBKDF2_ITERATIONS = 210000
ADMIN_ACCOUNT_DEFAULT_USERNAME = "admin"
ADMIN_ACCOUNT_DEFAULT_PASSWORD = "ChangeMe123!"

LOGIN_ALLOWED_USERS_SETTING_KEY = "auth_login_allowed_users_json"
ADMIN_ALLOWED_USERS_SETTING_KEY = "auth_admin_allowed_users_json"
ADMIN_ACCOUNT_SETTING_KEY = "admin_account_credentials_json"
DINGTALK_OAUTH_CONFIG_SETTING_KEY = "dingtalk_oauth_config_json"

DINGTALK_OAUTH_AUTHORIZE_URL = "https://login.dingtalk.com/oauth2/auth"
DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
DINGTALK_OAUTH_USER_ME_URL = "https://api.dingtalk.com/v1.0/contact/users/me"
DINGTALK_OAUTH_DEFAULT_SCOPE = "openid corpid Contact.User.Read"
DINGTALK_SCAN_SESSION_TTL_MINUTES = 5
DEFAULT_DINGTALK_OAUTH_CONFIG: dict[str, Any] = {}


def configure(
    *,
    db_path: Path,
    default_local_user_id: str,
    default_local_user_name: str,
    session_duration_days: int,
    admin_password_pbkdf2_iterations: int,
    admin_account_default_username: str,
    admin_account_default_password: str,
    login_allowed_users_setting_key: str,
    admin_allowed_users_setting_key: str,
    admin_account_setting_key: str,
    dingtalk_oauth_config_setting_key: str,
    dingtalk_oauth_authorize_url: str,
    dingtalk_oauth_user_access_token_url: str,
    dingtalk_oauth_user_me_url: str,
    dingtalk_oauth_default_scope: str,
    dingtalk_scan_session_ttl_minutes: int,
    default_dingtalk_oauth_config: dict[str, Any] | None = None,
) -> None:
    global DB_PATH
    global DEFAULT_LOCAL_USER_ID
    global DEFAULT_LOCAL_USER_NAME
    global SESSION_DURATION_DAYS
    global ADMIN_PASSWORD_PBKDF2_ITERATIONS
    global ADMIN_ACCOUNT_DEFAULT_USERNAME
    global ADMIN_ACCOUNT_DEFAULT_PASSWORD
    global LOGIN_ALLOWED_USERS_SETTING_KEY
    global ADMIN_ALLOWED_USERS_SETTING_KEY
    global ADMIN_ACCOUNT_SETTING_KEY
    global DINGTALK_OAUTH_CONFIG_SETTING_KEY
    global DINGTALK_OAUTH_AUTHORIZE_URL
    global DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL
    global DINGTALK_OAUTH_USER_ME_URL
    global DINGTALK_OAUTH_DEFAULT_SCOPE
    global DINGTALK_SCAN_SESSION_TTL_MINUTES
    global DEFAULT_DINGTALK_OAUTH_CONFIG

    DB_PATH = Path(db_path)
    DEFAULT_LOCAL_USER_ID = str(default_local_user_id)
    DEFAULT_LOCAL_USER_NAME = str(default_local_user_name)
    SESSION_DURATION_DAYS = int(session_duration_days)
    ADMIN_PASSWORD_PBKDF2_ITERATIONS = int(admin_password_pbkdf2_iterations)
    ADMIN_ACCOUNT_DEFAULT_USERNAME = str(admin_account_default_username)
    ADMIN_ACCOUNT_DEFAULT_PASSWORD = str(admin_account_default_password)
    LOGIN_ALLOWED_USERS_SETTING_KEY = str(login_allowed_users_setting_key)
    ADMIN_ALLOWED_USERS_SETTING_KEY = str(admin_allowed_users_setting_key)
    ADMIN_ACCOUNT_SETTING_KEY = str(admin_account_setting_key)
    DINGTALK_OAUTH_CONFIG_SETTING_KEY = str(dingtalk_oauth_config_setting_key)
    DINGTALK_OAUTH_AUTHORIZE_URL = str(dingtalk_oauth_authorize_url)
    DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL = str(dingtalk_oauth_user_access_token_url)
    DINGTALK_OAUTH_USER_ME_URL = str(dingtalk_oauth_user_me_url)
    DINGTALK_OAUTH_DEFAULT_SCOPE = str(dingtalk_oauth_default_scope)
    DINGTALK_SCAN_SESSION_TTL_MINUTES = int(dingtalk_scan_session_ttl_minutes)
    DEFAULT_DINGTALK_OAUTH_CONFIG = dict(default_dingtalk_oauth_config or {})


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.row_factory = sqlite3.Row
    return connection


def normalize_user_id(value: str | None) -> str:
    user_id = str(value or "").strip()
    if not user_id:
        return DEFAULT_LOCAL_USER_ID
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{1,128}", user_id):
        raise ValueError("用户标识格式不合法，仅支持字母、数字、._:@-。")
    return user_id


def normalize_configurable_option_label(value: str | None, *, field_label: str, max_length: int = 20) -> str:
    label = re.sub(r"\s+", " ", str(value or "").strip())
    if not label:
        raise ValueError(f"{field_label}不能为空。")
    if len(label) > max_length:
        raise ValueError(f"{field_label}长度不能超过 {max_length} 个字符。")
    return label


def normalize_position_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="岗位字段")


def normalize_item_type_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="服务类型字段")


def normalize_project_type_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="项目类型字段")


def normalize_sales_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="销售字段")


def normalize_service_mode_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="服务方式字段")


def normalize_department_option_label(value: str | None) -> str:
    return normalize_configurable_option_label(value, field_label="所属部门", max_length=30)


def normalize_configurable_option_list(
    raw_values: object,
    *,
    label_normalizer,
    allow_empty: bool,
    empty_error: str,
) -> list[str]:
    if isinstance(raw_values, str):
        values = [raw_values]
    elif isinstance(raw_values, (list, tuple, set)):
        values = list(raw_values)
    else:
        values = []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        label = label_normalizer(raw_value)
        lowered = label.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(label)
    if not normalized and not allow_empty:
        raise ValueError(empty_error)
    return normalized


def normalize_position_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_position_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个岗位字段。",
    )


def normalize_item_type_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_item_type_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个服务类型字段。",
    )


def normalize_project_type_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_project_type_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个项目类型字段。",
    )


def normalize_sales_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_sales_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个销售字段。",
    )


def normalize_service_mode_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_service_mode_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个服务方式字段。",
    )


def normalize_department_option_list(raw_values: object, *, allow_empty: bool = False) -> list[str]:
    return normalize_configurable_option_list(
        raw_values,
        label_normalizer=normalize_department_option_label,
        allow_empty=allow_empty,
        empty_error="至少保留一个所属部门。",
    )


def _get_position_field_scope_meta(
) -> dict[str, dict[str, Any]]:
    return {
        "sales": {
            "label": "销售字段",
            "normalize": normalize_sales_option_list,
        },
        "project_types": {
            "label": "项目类型字段",
            "normalize": normalize_project_type_option_list,
        },
        "service_modes": {
            "label": "服务方式字段",
            "normalize": normalize_service_mode_option_list,
        },
        "item_types": {
            "label": "服务类型字段",
            "normalize": normalize_item_type_option_list,
        },
    }


def normalize_position_field_scope_map(
    raw_scopes: object,
    *,
    position_options: list[str] | tuple[str, ...] | None = None,
    strict: bool = True,
) -> dict[str, dict[str, list[str]]]:
    source = raw_scopes if isinstance(raw_scopes, dict) else {}
    provided_positions = list(position_options) if position_options is not None else list(source.keys())
    normalized_position_order = normalize_position_option_list(provided_positions, allow_empty=True)
    ordered_position_keys = {position.casefold() for position in normalized_position_order}
    field_meta = _get_position_field_scope_meta()
    normalized_scopes: dict[str, dict[str, list[str]]] = {}

    for raw_position, raw_scope in source.items():
        try:
            normalized_position = normalize_position_option_label(str(raw_position or "").strip())
        except ValueError:
            if strict:
                raise
            continue
        scope_payload = raw_scope if isinstance(raw_scope, dict) else {}
        normalized_scope: dict[str, list[str]] = {}
        has_restricted_field = False
        for field_key, meta in field_meta.items():
            normalized_scope[field_key] = meta["normalize"](scope_payload.get(field_key, []), allow_empty=True)
            if normalized_scope[field_key]:
                has_restricted_field = True
        if has_restricted_field:
            normalized_scopes[normalized_position] = normalized_scope
        if normalized_position.casefold() not in ordered_position_keys:
            normalized_position_order.append(normalized_position)
            ordered_position_keys.add(normalized_position.casefold())

    return {
        position: normalized_scopes[position]
        for position in normalized_position_order
        if position in normalized_scopes
    }


def get_default_local_account_position_options() -> list[str]:
    return list(LOCAL_ACCOUNT_POSITIONS)


def get_default_item_type_options() -> list[str]:
    return list(ITEM_TYPE_OPTIONS)


def get_default_project_type_options() -> list[str]:
    return list(PROJECT_TYPE_OPTIONS)


def get_default_sales_options() -> list[str]:
    return list(SALES_OPTIONS)


def get_default_service_mode_options() -> list[str]:
    return list(SERVICE_MODE_OPTIONS)


def get_default_department_options() -> list[str]:
    return []


def normalize_user_positions(
    raw_values: object,
    *,
    allow_empty: bool = True,
    allowed_options: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    normalized = normalize_position_option_list(raw_values, allow_empty=allow_empty)
    if allowed_options is None:
        return normalized
    allowed = {str(item).strip() for item in allowed_options if str(item or "").strip()}
    invalid = [item for item in normalized if item not in allowed]
    if invalid:
        raise ValueError(f"岗位字段不存在：{'、'.join(invalid)}。")
    return normalized


def build_positions_display_text(positions: list[str]) -> str:
    return "、".join([str(item).strip() for item in positions if str(item or "").strip()])


def parse_stored_positions(raw_json: object, legacy_position: str | None = None) -> list[str]:
    parsed_values: object = []
    if isinstance(raw_json, str) and raw_json.strip():
        try:
            loaded = json.loads(raw_json)
            if isinstance(loaded, list):
                parsed_values = loaded
            elif isinstance(loaded, str) and loaded.strip():
                parsed_values = [loaded]
        except json.JSONDecodeError:
            parsed_values = []
    elif isinstance(raw_json, list):
        parsed_values = raw_json
    positions: list[str] = []
    seen: set[str] = set()
    for raw_value in parsed_values if isinstance(parsed_values, list) else []:
        try:
            label = normalize_position_option_label(raw_value)
        except ValueError:
            continue
        lowered = label.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        positions.append(label)
    if positions:
        return positions
    legacy = str(legacy_position or "").strip()
    if not legacy:
        return []
    try:
        return [normalize_position_option_label(legacy)]
    except ValueError:
        return []


def ensure_user(
    user_id: str,
    display_name: str | None = None,
    role: str = "user",
    positions: object | None = None,
    position: str | None = None,
    department: str | None = None,
) -> str:
    normalized_user_id = normalize_user_id(user_id)
    name_override = str(display_name or "").strip()
    normalized_name = name_override or normalized_user_id
    normalized_role = "admin" if role == "admin" else "user"
    if positions is None:
        raw_positions: object = [position] if str(position or "").strip() else []
    else:
        raw_positions = positions
    normalized_positions = normalize_position_option_list(raw_positions, allow_empty=True)
    normalized_position = normalized_positions[0] if normalized_positions else ""
    normalized_department = normalize_department_option_label(department) if str(department or "").strip() else ""
    normalized_positions_json = json.dumps(normalized_positions, ensure_ascii=False)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        existing_row = connection.execute(
            """
            SELECT user_id, display_name, role, position, positions_json, department
            FROM users
            WHERE user_id = ?
            """,
            (normalized_user_id,),
        ).fetchone()
        if existing_row:
            stored_role = "admin" if str(existing_row["role"] or "") == "admin" else "user"
            next_role = stored_role if stored_role == "admin" else normalized_role
            should_update_name = bool(name_override and str(existing_row["display_name"] or "") != normalized_name)
            should_update_positions = bool(
                normalized_positions
                and (
                    str(existing_row["position"] or "") != normalized_position
                    or str(existing_row["positions_json"] or "") != normalized_positions_json
                )
            )
            should_update_department = bool(
                normalized_department
                and str(existing_row["department"] or "") != normalized_department
            )
            should_update_role = stored_role != next_role
            if not (
                should_update_name
                or should_update_positions
                or should_update_department
                or should_update_role
            ):
                return normalized_user_id
        connection.execute(
            """
            INSERT INTO users (user_id, display_name, role, position, positions_json, department, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                display_name = CASE
                    WHEN ? = 1 THEN excluded.display_name
                    ELSE users.display_name
                END,
                position = CASE
                    WHEN ? = 1 THEN excluded.position
                    ELSE users.position
                END,
                positions_json = CASE
                    WHEN ? = 1 THEN excluded.positions_json
                    ELSE users.positions_json
                END,
                department = CASE
                    WHEN ? = 1 THEN excluded.department
                    ELSE users.department
                END,
                role = CASE WHEN users.role = 'admin' THEN users.role ELSE excluded.role END,
                updated_at = excluded.updated_at
            """,
            (
                normalized_user_id,
                normalized_name,
                normalized_role,
                normalized_position,
                normalized_positions_json,
                normalized_department,
                timestamp,
                timestamp,
                1 if name_override else 0,
                1 if normalized_positions else 0,
                1 if normalized_positions else 0,
                1 if normalized_department else 0,
            ),
        )
    return normalized_user_id


def get_default_user_id() -> str:
    preferred_positions = get_local_account_position_options()["options"][:1] or [DEFAULT_LOCAL_ACCOUNT_POSITION]
    return ensure_user(
        DEFAULT_LOCAL_USER_ID,
        DEFAULT_LOCAL_USER_NAME,
        role="admin",
        positions=preferred_positions,
    )


def build_password_hash(password: str, salt_hex: str, iterations: int) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
    return derived.hex()


def make_password_credentials(username: str, password: str) -> dict[str, Any]:
    normalized_username = normalize_local_username(username)
    normalized_password = str(password or "")
    if len(normalized_password) < 8:
        raise ValueError("密码长度至少 8 位。")
    salt_hex = secrets.token_hex(16)
    iterations = ADMIN_PASSWORD_PBKDF2_ITERATIONS
    return {
        "username": normalized_username,
        "salt_hex": salt_hex,
        "iterations": iterations,
        "password_hash": build_password_hash(normalized_password, salt_hex, iterations),
    }


def _ensure_app_settings_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def normalize_local_username(value: str | None) -> str:
    username = str(value or "").strip().lower()
    if not username:
        raise ValueError("账号不能为空。")
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
        raise ValueError("账号仅支持 3-64 位字母、数字、._@-。")
    return username


def build_local_account_user_id(username: str) -> str:
    normalized_username = normalize_local_username(username)
    if normalized_username == normalize_local_username(ADMIN_ACCOUNT_DEFAULT_USERNAME):
        return DEFAULT_LOCAL_USER_ID
    return f"local.{normalized_username}"


def _bootstrap_default_admin_local_account() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        default_user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ? LIMIT 1",
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
        if not default_user_exists:
            connection.execute(
                """
                INSERT INTO users (user_id, display_name, role, position, positions_json, created_at, updated_at)
                VALUES (?, ?, 'admin', ?, ?, ?, ?)
                """,
                (
                    DEFAULT_LOCAL_USER_ID,
                    DEFAULT_LOCAL_USER_NAME,
                    DEFAULT_LOCAL_ACCOUNT_POSITION,
                    json.dumps([DEFAULT_LOCAL_ACCOUNT_POSITION], ensure_ascii=False),
                    timestamp,
                    timestamp,
                ),
            )

        existing = connection.execute(
            "SELECT username FROM local_accounts WHERE user_id = ?",
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
        if existing:
            credentials = None
        else:
            migrated = connection.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key = ?",
                (ADMIN_ACCOUNT_SETTING_KEY,),
            ).fetchone()
            credentials: dict[str, Any] | None = None
            if migrated:
                try:
                    loaded = json.loads(migrated["setting_value"] or "{}")
                    if isinstance(loaded, dict):
                        candidate_username = normalize_local_username(
                            str(loaded.get("username", "")).strip() or ADMIN_ACCOUNT_DEFAULT_USERNAME
                        )
                        salt_hex = str(loaded.get("salt_hex", "")).strip()
                        password_hash = str(loaded.get("password_hash", "")).strip()
                        iterations = int(
                            loaded.get("iterations", ADMIN_PASSWORD_PBKDF2_ITERATIONS) or ADMIN_PASSWORD_PBKDF2_ITERATIONS
                        )
                        if salt_hex and password_hash:
                            credentials = {
                                "username": candidate_username,
                                "salt_hex": salt_hex,
                                "password_hash": password_hash,
                                "iterations": iterations,
                            }
                except (ValueError, json.JSONDecodeError):
                    credentials = None
            if credentials is None:
                credentials = make_password_credentials(
                    ADMIN_ACCOUNT_DEFAULT_USERNAME,
                    ADMIN_ACCOUNT_DEFAULT_PASSWORD,
                )

            connection.execute(
                """
                INSERT INTO local_accounts (
                    username, user_id, display_name, position, positions_json, is_admin, password_hash, salt_hex, iterations, is_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    user_id = excluded.user_id,
                    display_name = excluded.display_name,
                    position = excluded.position,
                    positions_json = excluded.positions_json,
                    is_admin = 1,
                    password_hash = excluded.password_hash,
                    salt_hex = excluded.salt_hex,
                    iterations = excluded.iterations,
                    is_enabled = 1,
                    updated_at = excluded.updated_at
                """,
                (
                    str(credentials["username"]),
                    DEFAULT_LOCAL_USER_ID,
                    DEFAULT_LOCAL_USER_NAME,
                    DEFAULT_LOCAL_ACCOUNT_POSITION,
                    json.dumps([DEFAULT_LOCAL_ACCOUNT_POSITION], ensure_ascii=False),
                    str(credentials["password_hash"]),
                    str(credentials["salt_hex"]),
                    int(credentials["iterations"]),
                    timestamp,
                    timestamp,
                ),
            )
        connection.execute(
            """
            UPDATE local_accounts
            SET is_admin = 1, is_enabled = 1, updated_at = ?
            WHERE user_id = ?
            """,
            (timestamp, DEFAULT_LOCAL_USER_ID),
        )


def init_auth_storage() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                position TEXT NOT NULL DEFAULT '',
                positions_json TEXT NOT NULL DEFAULT '[]',
                department TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        user_columns = {
            str(row[1] or "").strip()
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "position" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN position TEXT NOT NULL DEFAULT ''")
        if "positions_json" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN positions_json TEXT NOT NULL DEFAULT '[]'")
        if "department" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN department TEXT NOT NULL DEFAULT ''")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at)")
        expired_session = connection.execute(
            "SELECT 1 FROM user_sessions WHERE expires_at <= ? LIMIT 1",
            (timestamp,),
        ).fetchone()
        if expired_session:
            connection.execute("DELETE FROM user_sessions WHERE expires_at <= ?", (timestamp,))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS local_accounts (
                username TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL DEFAULT '',
                position TEXT NOT NULL DEFAULT '售后',
                positions_json TEXT NOT NULL DEFAULT '[]',
                department TEXT NOT NULL DEFAULT '',
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_department_admin INTEGER NOT NULL DEFAULT 0,
                show_in_department_schedule INTEGER NOT NULL DEFAULT 0,
                password_hash TEXT NOT NULL,
                salt_hex TEXT NOT NULL,
                iterations INTEGER NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        local_account_columns = {
            str(row[1] or "").strip()
            for row in connection.execute("PRAGMA table_info(local_accounts)").fetchall()
        }
        local_account_admin_column_added = False
        if "display_name" not in local_account_columns:
            connection.execute("ALTER TABLE local_accounts ADD COLUMN display_name TEXT NOT NULL DEFAULT ''")
        if "position" not in local_account_columns:
            connection.execute(
                f"ALTER TABLE local_accounts ADD COLUMN position TEXT NOT NULL DEFAULT '{DEFAULT_LOCAL_ACCOUNT_POSITION}'"
            )
        if "positions_json" not in local_account_columns:
            connection.execute("ALTER TABLE local_accounts ADD COLUMN positions_json TEXT NOT NULL DEFAULT '[]'")
        if "department" not in local_account_columns:
            connection.execute("ALTER TABLE local_accounts ADD COLUMN department TEXT NOT NULL DEFAULT ''")
        if "is_admin" not in local_account_columns:
            connection.execute("ALTER TABLE local_accounts ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
            local_account_admin_column_added = True
        if "is_department_admin" not in local_account_columns:
            connection.execute(
                "ALTER TABLE local_accounts ADD COLUMN is_department_admin INTEGER NOT NULL DEFAULT 0"
            )
        if "show_in_department_schedule" not in local_account_columns:
            connection.execute(
                "ALTER TABLE local_accounts ADD COLUMN show_in_department_schedule INTEGER NOT NULL DEFAULT 0"
            )
        if local_account_admin_column_added:
            legacy_admin_user_ids = sorted(_get_legacy_local_account_admin_user_ids(connection))
            if legacy_admin_user_ids:
                placeholders = ", ".join("?" for _ in legacy_admin_user_ids)
                connection.execute(
                    f"UPDATE local_accounts SET is_admin = 1 WHERE user_id IN ({placeholders})",
                    tuple(legacy_admin_user_ids),
                )
        local_account_missing_display_name = connection.execute(
            "SELECT 1 FROM local_accounts WHERE TRIM(COALESCE(display_name, '')) = '' LIMIT 1"
        ).fetchone()
        if local_account_missing_display_name:
            connection.execute(
                """
                UPDATE local_accounts
                SET display_name = CASE
                    WHEN user_id = ? THEN ?
                    ELSE COALESCE(
                        NULLIF((SELECT display_name FROM users WHERE users.user_id = local_accounts.user_id), ''),
                        NULLIF(username, ''),
                        user_id
                    )
                END
                WHERE TRIM(COALESCE(display_name, '')) = ''
                """,
                (DEFAULT_LOCAL_USER_ID, DEFAULT_LOCAL_USER_NAME),
            )
        local_account_missing_position = connection.execute(
            "SELECT 1 FROM local_accounts WHERE TRIM(COALESCE(position, '')) = '' LIMIT 1"
        ).fetchone()
        if local_account_missing_position:
            connection.execute(
                """
                UPDATE local_accounts
                SET position = COALESCE(
                    NULLIF((SELECT position FROM users WHERE users.user_id = local_accounts.user_id), ''),
                    ?
                )
                WHERE TRIM(COALESCE(position, '')) = ''
                """,
                (DEFAULT_LOCAL_ACCOUNT_POSITION,),
            )
        local_account_missing_department = connection.execute(
            """
            SELECT 1
            FROM local_accounts
            WHERE TRIM(COALESCE(department, '')) = ''
              AND EXISTS (
                SELECT 1
                FROM users
                WHERE users.user_id = local_accounts.user_id
                  AND TRIM(COALESCE(users.department, '')) <> ''
              )
            LIMIT 1
            """
        ).fetchone()
        if local_account_missing_department:
            connection.execute(
                """
                UPDATE local_accounts
                SET department = (
                    SELECT TRIM(COALESCE(users.department, ''))
                    FROM users
                    WHERE users.user_id = local_accounts.user_id
                )
                WHERE TRIM(COALESCE(department, '')) = ''
                  AND EXISTS (
                    SELECT 1
                    FROM users
                    WHERE users.user_id = local_accounts.user_id
                      AND TRIM(COALESCE(users.department, '')) <> ''
                  )
                """
            )
        local_position_rows = connection.execute(
            """
            SELECT username, position, positions_json
            FROM local_accounts
            """
        ).fetchall()
        for row in local_position_rows:
            positions = parse_stored_positions(row["positions_json"], row["position"])
            positions_json = json.dumps(positions, ensure_ascii=False)
            next_position = positions[0] if positions else ""
            if next_position == str(row["position"] or "") and positions_json == str(row["positions_json"] or ""):
                continue
            connection.execute(
                """
                UPDATE local_accounts
                SET position = ?, positions_json = ?
                WHERE username = ?
                """,
                (
                    next_position,
                    positions_json,
                    str(row["username"] or ""),
                ),
            )
        user_position_rows = connection.execute(
            """
            SELECT user_id, position, positions_json
            FROM users
            """
        ).fetchall()
        for row in user_position_rows:
            positions = parse_stored_positions(row["positions_json"], row["position"])
            positions_json = json.dumps(positions, ensure_ascii=False)
            next_position = positions[0] if positions else ""
            if next_position == str(row["position"] or "") and positions_json == str(row["positions_json"] or ""):
                continue
            connection.execute(
                """
                UPDATE users
                SET position = ?, positions_json = ?
                WHERE user_id = ?
                """,
                (
                    next_position,
                    positions_json,
                    str(row["user_id"] or ""),
                ),
            )
        user_sync_rows = connection.execute(
            """
            SELECT
                users.user_id,
                users.position AS user_position,
                users.positions_json AS user_positions_json,
                users.department AS user_department,
                local_accounts.position AS account_position,
                local_accounts.positions_json AS account_positions_json,
                local_accounts.department AS account_department
            FROM users
            JOIN local_accounts ON local_accounts.user_id = users.user_id
            """
        ).fetchall()
        for row in user_sync_rows:
            next_position = str(row["account_position"] or "").strip() or str(row["user_position"] or "")
            next_positions_json = str(row["account_positions_json"] or "").strip() or str(row["user_positions_json"] or "")
            next_department = str(row["account_department"] or "").strip() or str(row["user_department"] or "")
            if (
                next_position == str(row["user_position"] or "")
                and next_positions_json == str(row["user_positions_json"] or "")
                and next_department == str(row["user_department"] or "")
            ):
                continue
            connection.execute(
                """
                UPDATE users
                SET position = ?, positions_json = ?, department = ?
                WHERE user_id = ?
                """,
                (
                    next_position,
                    next_positions_json,
                    next_department,
                    str(row["user_id"] or ""),
                ),
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dingtalk_user_identities (
                local_user_id TEXT PRIMARY KEY,
                corp_id TEXT NOT NULL DEFAULT '',
                union_id TEXT NOT NULL DEFAULT '',
                open_id TEXT NOT NULL DEFAULT '',
                nick TEXT NOT NULL DEFAULT '',
                avatar_url TEXT NOT NULL DEFAULT '',
                mobile TEXT NOT NULL DEFAULT '',
                raw_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_dingtalk_user_identities_union ON dingtalk_user_identities(corp_id, union_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_dingtalk_user_identities_open ON dingtalk_user_identities(corp_id, open_id)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dingtalk_scan_login_sessions (
                login_id TEXT PRIMARY KEY,
                state_token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                redirect_base_url TEXT NOT NULL DEFAULT '',
                auth_user_id TEXT NOT NULL DEFAULT '',
                auth_display_name TEXT NOT NULL DEFAULT '',
                auth_raw_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_dingtalk_scan_login_sessions_state ON dingtalk_scan_login_sessions(state_token)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_dingtalk_scan_login_sessions_expires ON dingtalk_scan_login_sessions(expires_at)"
        )
        default_user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ? LIMIT 1",
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
        if not default_user_exists:
            connection.execute(
                """
                INSERT INTO users (user_id, display_name, role, position, positions_json, created_at, updated_at)
                VALUES (?, ?, 'admin', ?, ?, ?, ?)
                """,
                (
                    DEFAULT_LOCAL_USER_ID,
                    DEFAULT_LOCAL_USER_NAME,
                    DEFAULT_LOCAL_ACCOUNT_POSITION,
                    json.dumps([DEFAULT_LOCAL_ACCOUNT_POSITION], ensure_ascii=False),
                    timestamp,
                    timestamp,
                ),
            )
    _bootstrap_default_admin_local_account()
    _sanitize_stored_access_control_settings()


def get_user_by_id(user_id: str | None) -> dict[str, Any] | None:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                users.user_id,
                users.display_name,
                users.role,
                users.position,
                users.positions_json,
                users.department,
                users.created_at,
                users.updated_at,
                local_accounts.username AS local_account_username,
                COALESCE(local_accounts.is_enabled, 1) AS local_account_enabled_flag,
                COALESCE(local_accounts.is_admin, 0) AS local_account_admin_flag,
                COALESCE(local_accounts.is_department_admin, 0) AS department_admin_flag,
                COALESCE(local_accounts.show_in_department_schedule, 0) AS department_schedule_visible_flag
            FROM users
            LEFT JOIN local_accounts ON local_accounts.user_id = users.user_id
            WHERE users.user_id = ?
            """,
            (normalized_user_id,),
        ).fetchone()
    if not row:
        return None
    local_account_admin = bool(int(row["local_account_admin_flag"] or 0))
    has_local_account = bool(str(row["local_account_username"] or "").strip())
    role = "admin" if has_admin_access(str(row["user_id"]), local_account_admin=local_account_admin) else "user"
    positions = parse_stored_positions(row["positions_json"], row["position"])
    return {
        "user_id": str(row["user_id"]),
        "display_name": str(row["display_name"] or row["user_id"]),
        "role": role,
        "position": positions[0] if positions else "",
        "positions": positions,
        "position_labels": build_positions_display_text(positions),
        "department": str(row["department"] or "").strip(),
        "has_local_account": has_local_account,
        "enabled": bool(int(row["local_account_enabled_flag"] or 0)) if has_local_account else True,
        "is_department_admin": bool(int(row["department_admin_flag"] or 0)),
        "show_in_department_schedule": bool(int(row["department_schedule_visible_flag"] or 0)) if has_local_account else False,
        "created_at": str(row["created_at"] or ""),
        "updated_at": str(row["updated_at"] or ""),
    }


def list_all_users() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                users.user_id,
                users.display_name,
                users.role,
                users.position,
                users.positions_json,
                users.department,
                users.created_at,
                users.updated_at,
                local_accounts.username AS local_account_username,
                COALESCE(local_accounts.is_enabled, 1) AS local_account_enabled_flag,
                COALESCE(local_accounts.is_admin, 0) AS local_account_admin_flag,
                COALESCE(local_accounts.is_department_admin, 0) AS department_admin_flag,
                COALESCE(local_accounts.show_in_department_schedule, 0) AS department_schedule_visible_flag
            FROM users
            LEFT JOIN local_accounts ON local_accounts.user_id = users.user_id
            ORDER BY
                CASE WHEN users.role = 'admin' THEN 0 ELSE 1 END ASC,
                users.updated_at DESC,
                users.user_id ASC
            """
        ).fetchall()
    users: list[dict[str, Any]] = []
    for row in rows:
        user_id = str(row["user_id"])
        positions = parse_stored_positions(row["positions_json"], row["position"])
        local_account_admin = bool(int(row["local_account_admin_flag"] or 0))
        has_local_account = bool(str(row["local_account_username"] or "").strip())
        users.append(
            {
                "user_id": user_id,
                "display_name": str(row["display_name"] or row["user_id"]),
                "role": "admin" if has_admin_access(user_id, local_account_admin=local_account_admin) else "user",
                "position": positions[0] if positions else "",
                "positions": positions,
                "position_labels": build_positions_display_text(positions),
                "department": str(row["department"] or "").strip(),
                "has_local_account": has_local_account,
                "enabled": bool(int(row["local_account_enabled_flag"] or 0)) if has_local_account else True,
                "is_department_admin": bool(int(row["department_admin_flag"] or 0)),
                "show_in_department_schedule": bool(int(row["department_schedule_visible_flag"] or 0)) if has_local_account else False,
                "created_at": str(row["created_at"] or ""),
                "updated_at": str(row["updated_at"] or ""),
            }
        )
    users.sort(key=lambda item: (0 if item["role"] == "admin" else 1, item["user_id"]))
    return users


def normalize_user_id_list(raw_values: object) -> list[str]:
    if not isinstance(raw_values, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_values:
        try:
            user_id = normalize_user_id(str(raw_value or "").strip())
        except ValueError:
            continue
        if user_id in seen:
            continue
        seen.add(user_id)
        normalized.append(user_id)
    return normalized


def _get_option_setting(
    setting_key: str,
    default_options: list[str],
    normalize_option_list,
) -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (setting_key,),
        ).fetchone()
    updated_at = ""
    if not row:
        return {"options": default_options, "updated_at": updated_at}
    updated_at = str(row["updated_at"] or "")
    try:
        options = normalize_option_list(json.loads(row["setting_value"] or "[]"), allow_empty=False)
    except (ValueError, json.JSONDecodeError, TypeError):
        options = default_options
    return {"options": options, "updated_at": updated_at}


def _save_option_setting(
    setting_key: str,
    raw_options: object,
    normalize_option_list,
) -> tuple[dict[str, Any], str]:
    options = normalize_option_list(raw_options, allow_empty=False)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (
                setting_key,
                json.dumps(options, ensure_ascii=False),
                timestamp,
            ),
        )
    return {"options": options, "updated_at": timestamp}, timestamp


def _save_json_setting_payload(setting_key: str, payload: object, timestamp: str) -> None:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (
                setting_key,
                json.dumps(payload, ensure_ascii=False),
                timestamp,
            ),
        )


def get_local_account_position_options() -> dict[str, Any]:
    return _get_option_setting(
        LOCAL_ACCOUNT_POSITION_OPTIONS_SETTING_KEY,
        get_default_local_account_position_options(),
        normalize_position_option_list,
    )


def get_item_type_options() -> dict[str, Any]:
    return _get_option_setting(
        ITEM_TYPE_OPTIONS_SETTING_KEY,
        get_default_item_type_options(),
        normalize_item_type_option_list,
    )


def get_project_type_options() -> dict[str, Any]:
    return _get_option_setting(
        PROJECT_TYPE_OPTIONS_SETTING_KEY,
        get_default_project_type_options(),
        normalize_project_type_option_list,
    )


def get_sales_options() -> dict[str, Any]:
    return _get_option_setting(
        SALES_OPTIONS_SETTING_KEY,
        get_default_sales_options(),
        normalize_sales_option_list,
    )


def _cleanup_local_account_positions(allowed_options: list[str], timestamp: str) -> None:
    with get_connection() as connection:
        local_rows = connection.execute(
            """
            SELECT username, position, positions_json
            FROM local_accounts
            """
        ).fetchall()
        for row in local_rows:
            positions = parse_stored_positions(row["positions_json"], row["position"])
            filtered_positions = [item for item in positions if item in allowed_options]
            if filtered_positions == positions:
                continue
            connection.execute(
                """
                UPDATE local_accounts
                SET position = ?, positions_json = ?, updated_at = ?
                WHERE username = ?
                """,
                (
                    filtered_positions[0] if filtered_positions else "",
                    json.dumps(filtered_positions, ensure_ascii=False),
                    timestamp,
                    str(row["username"] or ""),
                ),
            )

        user_rows = connection.execute(
            """
            SELECT user_id, position, positions_json
            FROM users
            """
        ).fetchall()
        for row in user_rows:
            positions = parse_stored_positions(row["positions_json"], row["position"])
            filtered_positions = [item for item in positions if item in allowed_options]
            if filtered_positions == positions:
                continue
            connection.execute(
                """
                UPDATE users
                SET position = ?, positions_json = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (
                    filtered_positions[0] if filtered_positions else "",
                    json.dumps(filtered_positions, ensure_ascii=False),
                    timestamp,
                    str(row["user_id"] or ""),
                ),
            )


def save_local_account_position_options(raw_options: object) -> tuple[dict[str, Any], str]:
    data, timestamp = _save_option_setting(
        LOCAL_ACCOUNT_POSITION_OPTIONS_SETTING_KEY,
        raw_options,
        normalize_position_option_list,
    )
    _cleanup_local_account_positions(data["options"], timestamp)
    _cleanup_position_field_scopes(timestamp)
    return data, timestamp


def save_item_type_options(raw_options: object) -> tuple[dict[str, Any], str]:
    data, timestamp = _save_option_setting(
        ITEM_TYPE_OPTIONS_SETTING_KEY,
        raw_options,
        normalize_item_type_option_list,
    )
    _cleanup_position_field_scopes(timestamp)
    return data, timestamp


def save_project_type_options(raw_options: object) -> tuple[dict[str, Any], str]:
    data, timestamp = _save_option_setting(
        PROJECT_TYPE_OPTIONS_SETTING_KEY,
        raw_options,
        normalize_project_type_option_list,
    )
    _cleanup_position_field_scopes(timestamp)
    return data, timestamp


def save_sales_options(raw_options: object) -> tuple[dict[str, Any], str]:
    data, timestamp = _save_option_setting(
        SALES_OPTIONS_SETTING_KEY,
        raw_options,
        normalize_sales_option_list,
    )
    _cleanup_position_field_scopes(timestamp)
    return data, timestamp


def get_service_mode_options() -> dict[str, Any]:
    return _get_option_setting(
        SERVICE_MODE_OPTIONS_SETTING_KEY,
        get_default_service_mode_options(),
        normalize_service_mode_option_list,
    )


def _merge_department_option_groups(*groups: object) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        raw_values = group if isinstance(group, (list, tuple, set)) else []
        for raw_value in raw_values:
            try:
                department = normalize_department_option_label(raw_value)
            except ValueError:
                continue
            key = department.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(department)
    return merged


def _list_account_department_options() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT department
            FROM local_accounts
            WHERE TRIM(COALESCE(department, '')) <> ''
            ORDER BY updated_at DESC, username ASC
            """
        ).fetchall()
    return _merge_department_option_groups([str(row["department"] or "").strip() for row in rows])


def get_department_options() -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (DEPARTMENT_OPTIONS_SETTING_KEY,),
        ).fetchone()
    updated_at = str(row["updated_at"] or "") if row else ""
    stored_options: list[str] = []
    if row:
        try:
            stored_options = normalize_department_option_list(json.loads(row["setting_value"] or "[]"), allow_empty=True)
        except (ValueError, json.JSONDecodeError, TypeError):
            stored_options = []
    merged_options = _merge_department_option_groups(
        stored_options,
        _list_account_department_options(),
        get_default_department_options(),
    )
    return {"options": merged_options, "updated_at": updated_at}


def save_department_options(raw_options: object) -> tuple[dict[str, Any], str]:
    normalized_options = _merge_department_option_groups(raw_options, _list_account_department_options())
    if not normalized_options:
        raise ValueError("至少保留一个所属部门。")
    return _save_option_setting(
        DEPARTMENT_OPTIONS_SETTING_KEY,
        normalized_options,
        normalize_department_option_list,
    )


def save_service_mode_options(raw_options: object) -> tuple[dict[str, Any], str]:
    data, timestamp = _save_option_setting(
        SERVICE_MODE_OPTIONS_SETTING_KEY,
        raw_options,
        normalize_service_mode_option_list,
    )
    _cleanup_position_field_scopes(timestamp)
    return data, timestamp


def get_business_field_options() -> dict[str, list[str]]:
    return {
        "item_types": get_item_type_options()["options"],
        "project_types": get_project_type_options()["options"],
        "sales": get_sales_options()["options"],
        "service_modes": get_service_mode_options()["options"],
    }


def _build_position_scoped_field_options(
    position_order: list[str],
    scopes: dict[str, dict[str, list[str]]],
    existing_options: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    field_keys = ("item_types", "project_types", "sales", "service_modes")
    aggregated: dict[str, list[str]] = {field_key: [] for field_key in field_keys}
    seen_map: dict[str, set[str]] = {field_key: set() for field_key in field_keys}

    for position in position_order:
        scope = scopes.get(position) or {}
        for field_key in field_keys:
            for raw_value in scope.get(field_key, []) or []:
                value = str(raw_value or "").strip()
                value_key = value.casefold()
                if not value or value_key in seen_map[field_key]:
                    continue
                seen_map[field_key].add(value_key)
                aggregated[field_key].append(value)

    fallback = existing_options if existing_options is not None else get_business_field_options()
    for field_key in field_keys:
        if aggregated[field_key]:
            continue
        aggregated[field_key] = list(fallback.get(field_key) or [])
    return aggregated


def get_position_field_scopes() -> dict[str, Any]:
    positions = get_local_account_position_options()["options"]
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (POSITION_FIELD_SCOPE_SETTING_KEY,),
        ).fetchone()
    if not row:
        return {
            "positions": positions,
            "scopes": {},
            "field_options": get_business_field_options(),
            "updated_at": "",
        }
    updated_at = str(row["updated_at"] or "")
    try:
        scopes = normalize_position_field_scope_map(
            json.loads(row["setting_value"] or "{}"),
            position_options=positions,
            strict=False,
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        scopes = {}
    return {
        "positions": positions,
        "scopes": scopes,
        "field_options": get_business_field_options(),
        "updated_at": updated_at,
    }


def save_position_field_scopes(payload: object) -> tuple[dict[str, Any], str]:
    source = payload if isinstance(payload, dict) else {}
    raw_scopes = source.get("scopes", source)
    raw_positions = source.get("positions")
    existing_positions = get_local_account_position_options()["options"]
    if isinstance(raw_positions, (list, tuple, set)):
        positions = normalize_position_option_list(list(raw_positions), allow_empty=False)
    else:
        scope_keys = list(raw_scopes.keys()) if isinstance(raw_scopes, dict) else []
        merged_positions = list(existing_positions)
        merged_seen = {item.casefold() for item in merged_positions}
        for raw_position in scope_keys:
            position = normalize_position_option_label(str(raw_position or "").strip())
            if position.casefold() in merged_seen:
                continue
            merged_seen.add(position.casefold())
            merged_positions.append(position)
        positions = normalize_position_option_list(merged_positions, allow_empty=False)
    scopes = normalize_position_field_scope_map(raw_scopes, position_options=positions, strict=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    aggregated_field_options = _build_position_scoped_field_options(
        positions,
        scopes,
        existing_options={},
    )
    _save_json_setting_payload(LOCAL_ACCOUNT_POSITION_OPTIONS_SETTING_KEY, positions, timestamp)
    _save_json_setting_payload(ITEM_TYPE_OPTIONS_SETTING_KEY, aggregated_field_options["item_types"], timestamp)
    _save_json_setting_payload(PROJECT_TYPE_OPTIONS_SETTING_KEY, aggregated_field_options["project_types"], timestamp)
    _save_json_setting_payload(SALES_OPTIONS_SETTING_KEY, aggregated_field_options["sales"], timestamp)
    _save_json_setting_payload(SERVICE_MODE_OPTIONS_SETTING_KEY, aggregated_field_options["service_modes"], timestamp)
    _save_json_setting_payload(POSITION_FIELD_SCOPE_SETTING_KEY, scopes, timestamp)
    _cleanup_local_account_positions(positions, timestamp)
    return {
        "positions": positions,
        "scopes": scopes,
        "field_options": aggregated_field_options,
        "updated_at": timestamp,
    }, timestamp


def _cleanup_position_field_scopes(timestamp: str) -> None:
    settings = get_position_field_scopes()
    save_position_field_scopes(
        {
            "positions": settings["positions"],
            "scopes": settings["scopes"],
        }
    )


def get_business_field_options_for_positions(positions: object | None = None) -> dict[str, list[str]]:
    business_field_options = get_business_field_options()
    allowed_position_options = get_local_account_position_options()["options"]
    try:
        normalized_positions = normalize_user_positions(
            positions if positions is not None else [],
            allow_empty=True,
            allowed_options=allowed_position_options,
        )
    except ValueError:
        requested_positions = {
            str(item).strip()
            for item in (positions if isinstance(positions, (list, tuple, set)) else [])
            if str(item or "").strip()
        }
        normalized_positions = [item for item in allowed_position_options if item in requested_positions]
    if not normalized_positions:
        return {
            field_key: list(options)
            for field_key, options in business_field_options.items()
        }

    scope_map = get_position_field_scopes()["scopes"]
    filtered_options: dict[str, list[str]] = {}
    for field_key, master_options in business_field_options.items():
        allowed_values: set[str] = set()
        has_explicit_restriction = False
        has_unrestricted_position = False
        for position in normalized_positions:
            position_scope = scope_map.get(position) or {}
            scoped_values = list(position_scope.get(field_key) or [])
            if not scoped_values:
                has_unrestricted_position = True
                continue
            has_explicit_restriction = True
            allowed_values.update(item.casefold() for item in scoped_values)
        if has_unrestricted_position or not has_explicit_restriction:
            filtered_options[field_key] = list(master_options)
            continue
        filtered_options[field_key] = [
            option for option in master_options if str(option).strip().casefold() in allowed_values
        ]
    return filtered_options


def get_business_field_options_for_user_id(user_id: str | None = None) -> dict[str, list[str]]:
    if str(user_id or "").strip():
        user = get_user_by_id(user_id)
        if user:
            return get_business_field_options_for_positions(user.get("positions", []))
    return get_business_field_options_for_positions([])


def _list_local_account_user_ids(connection: sqlite3.Connection | None = None) -> set[str]:
    def _load_ids(active_connection: sqlite3.Connection) -> set[str]:
        try:
            rows = active_connection.execute(
                """
                SELECT user_id
                FROM local_accounts
                WHERE TRIM(COALESCE(user_id, '')) <> ''
                """
            ).fetchall()
        except sqlite3.OperationalError:
            return set()
        return {
            normalize_user_id(str(row["user_id"] or ""))
            for row in rows
            if str(row["user_id"] or "").strip()
        }

    if connection is not None:
        return _load_ids(connection)
    with get_connection() as active_connection:
        return _load_ids(active_connection)


def _sanitize_access_control_user_lists(
    login_allowed_users: object,
    admin_allowed_users: object,
    *,
    local_account_user_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    normalized_login = normalize_user_id_list(login_allowed_users)
    normalized_admin = normalize_user_id_list(admin_allowed_users)
    local_user_ids = local_account_user_ids if local_account_user_ids is not None else _list_local_account_user_ids()
    filtered_login = [user_id for user_id in normalized_login if user_id not in local_user_ids]
    login_user_ids = set(filtered_login)
    filtered_admin = [
        user_id
        for user_id in normalized_admin
        if user_id not in local_user_ids and user_id in login_user_ids
    ]
    return filtered_login, filtered_admin


def _get_legacy_local_account_admin_user_ids(connection: sqlite3.Connection) -> set[str]:
    local_user_ids = _list_local_account_user_ids(connection)
    if not local_user_ids:
        return set()
    legacy_admin_user_ids = {DEFAULT_LOCAL_USER_ID}
    setting_row = connection.execute(
        "SELECT setting_value FROM app_settings WHERE setting_key = ?",
        (ADMIN_ALLOWED_USERS_SETTING_KEY,),
    ).fetchone()
    try:
        admin_allowed_users = normalize_user_id_list(json.loads(setting_row["setting_value"] or "[]")) if setting_row else []
    except (TypeError, json.JSONDecodeError):
        admin_allowed_users = []
    legacy_admin_user_ids.update(user_id for user_id in admin_allowed_users if user_id in local_user_ids)
    role_rows = connection.execute(
        """
        SELECT local_accounts.user_id
        FROM local_accounts
        JOIN users ON users.user_id = local_accounts.user_id
        WHERE users.role = 'admin'
        """
    ).fetchall()
    legacy_admin_user_ids.update(
        normalize_user_id(str(row["user_id"] or ""))
        for row in role_rows
        if str(row["user_id"] or "").strip() in local_user_ids
    )
    return legacy_admin_user_ids


def _sanitize_stored_access_control_settings() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        rows = connection.execute(
            """
            SELECT setting_key, setting_value
            FROM app_settings
            WHERE setting_key IN (?, ?)
            """
            ,
            (LOGIN_ALLOWED_USERS_SETTING_KEY, ADMIN_ALLOWED_USERS_SETTING_KEY),
        ).fetchall()
        values = {str(row["setting_key"] or ""): str(row["setting_value"] or "") for row in rows}
        try:
            raw_login_allowed_users = json.loads(values.get(LOGIN_ALLOWED_USERS_SETTING_KEY, "[]"))
        except (TypeError, json.JSONDecodeError):
            raw_login_allowed_users = []
        try:
            raw_admin_allowed_users = json.loads(values.get(ADMIN_ALLOWED_USERS_SETTING_KEY, "[]"))
        except (TypeError, json.JSONDecodeError):
            raw_admin_allowed_users = []
        local_user_ids = _list_local_account_user_ids(connection)
        normalized_login = normalize_user_id_list(raw_login_allowed_users)
        normalized_admin = normalize_user_id_list(raw_admin_allowed_users)
        sanitized_login, sanitized_admin = _sanitize_access_control_user_lists(
            raw_login_allowed_users,
            raw_admin_allowed_users,
            local_account_user_ids=local_user_ids,
        )
        if normalized_login == sanitized_login and normalized_admin == sanitized_admin:
            return
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (LOGIN_ALLOWED_USERS_SETTING_KEY, json.dumps(sanitized_login, ensure_ascii=False), timestamp),
        )
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (ADMIN_ALLOWED_USERS_SETTING_KEY, json.dumps(sanitized_admin, ensure_ascii=False), timestamp),
        )


def get_access_control_settings() -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        rows = connection.execute(
            """
            SELECT setting_key, setting_value, updated_at
            FROM app_settings
            WHERE setting_key IN (?, ?)
            """,
            (LOGIN_ALLOWED_USERS_SETTING_KEY, ADMIN_ALLOWED_USERS_SETTING_KEY),
        ).fetchall()
        local_account_user_ids = _list_local_account_user_ids(connection)
    values: dict[str, str] = {}
    updated_at_values: list[str] = []
    for row in rows:
        values[str(row["setting_key"])] = str(row["setting_value"] or "")
        updated_at = str(row["updated_at"] or "")
        if updated_at:
            updated_at_values.append(updated_at)
    try:
        raw_login_allowed_users = json.loads(values.get(LOGIN_ALLOWED_USERS_SETTING_KEY, "[]"))
    except (TypeError, json.JSONDecodeError):
        raw_login_allowed_users = []
    try:
        raw_admin_allowed_users = json.loads(values.get(ADMIN_ALLOWED_USERS_SETTING_KEY, "[]"))
    except (TypeError, json.JSONDecodeError):
        raw_admin_allowed_users = []
    login_allowed_users, admin_allowed_users = _sanitize_access_control_user_lists(
        raw_login_allowed_users,
        raw_admin_allowed_users,
        local_account_user_ids=local_account_user_ids,
    )
    return {
        "login_allowed_users": login_allowed_users,
        "admin_allowed_users": admin_allowed_users,
        "updated_at": max(updated_at_values) if updated_at_values else "",
    }


def save_access_control_settings(login_allowed_users: object, admin_allowed_users: object) -> tuple[dict[str, Any], str]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        normalized_login, normalized_admin = _sanitize_access_control_user_lists(
            login_allowed_users,
            admin_allowed_users,
            local_account_user_ids=_list_local_account_user_ids(connection),
        )
        _ensure_app_settings_table(connection)
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (LOGIN_ALLOWED_USERS_SETTING_KEY, json.dumps(normalized_login, ensure_ascii=False), timestamp),
        )
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (ADMIN_ALLOWED_USERS_SETTING_KEY, json.dumps(normalized_admin, ensure_ascii=False), timestamp),
        )
    settings = {
        "login_allowed_users": normalized_login,
        "admin_allowed_users": normalized_admin,
        "updated_at": timestamp,
    }
    return settings, timestamp


def is_user_allowed_to_login(user_id: str) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    settings = get_access_control_settings()
    return normalized_user_id in set(settings["login_allowed_users"])


def is_admin_user_id(user_id: str) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    settings = get_access_control_settings()
    return normalized_user_id in set(settings["admin_allowed_users"])


def is_local_account_admin_user_id(user_id: str | None) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT is_admin FROM local_accounts WHERE user_id = ?",
            (normalized_user_id,),
        ).fetchone()
    return bool(row and int(row["is_admin"] or 0))


def has_admin_access(user_id: str | None, *, local_account_admin: bool | None = None) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    if is_admin_user_id(normalized_user_id):
        return True
    if local_account_admin is not None:
        return bool(local_account_admin)
    return is_local_account_admin_user_id(normalized_user_id)


def is_department_admin_user_id(user_id: str | None) -> bool:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT is_department_admin FROM local_accounts WHERE user_id = ?",
            (normalized_user_id,),
        ).fetchone()
    return bool(row and int(row["is_department_admin"] or 0))


def _serialize_local_account(row: sqlite3.Row) -> dict[str, Any]:
    user_id = str(row["user_id"] or "")
    user = get_user_by_id(user_id)
    stored_display_name = str(row["display_name"] or "").strip()
    stored_positions = parse_stored_positions(row["positions_json"], row["position"])
    stored_department = str(row["department"] or "").strip()
    try:
        is_admin = bool(int(row["is_admin"] or 0))
    except (IndexError, KeyError, TypeError, ValueError):
        is_admin = is_local_account_admin_user_id(user_id)
    try:
        is_department_admin = bool(int(row["is_department_admin"] or 0))
    except (IndexError, KeyError, TypeError, ValueError):
        is_department_admin = is_department_admin_user_id(user_id)
    try:
        show_in_department_schedule = bool(int(row["show_in_department_schedule"] or 0))
    except (IndexError, KeyError, TypeError, ValueError):
        show_in_department_schedule = False
    if not stored_positions and isinstance(user, dict):
        stored_positions = list(user.get("positions") or [])
    return {
        "username": str(row["username"] or ""),
        "user_id": user_id,
        "display_name": stored_display_name or str((user or {}).get("display_name") or row["username"] or user_id),
        "position": stored_positions[0] if stored_positions else "",
        "positions": stored_positions,
        "position_labels": build_positions_display_text(stored_positions),
        "department": stored_department or str((user or {}).get("department") or ""),
        "enabled": bool(int(row["is_enabled"] or 0)),
        "is_admin": is_admin,
        "is_department_admin": is_department_admin,
        "show_in_department_schedule": show_in_department_schedule,
        "created_at": str(row["created_at"] or ""),
        "updated_at": str(row["updated_at"] or ""),
    }


def get_local_account_by_username(username: str | None) -> dict[str, Any] | None:
    normalized_username = normalize_local_username(username)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, is_department_admin, show_in_department_schedule, is_enabled, created_at, updated_at
            FROM local_accounts
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()
    if not row:
        return None
    return _serialize_local_account(row)


def get_local_account_by_user_id(user_id: str | None) -> dict[str, Any] | None:
    normalized_user_id = normalize_user_id(user_id)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, is_department_admin, show_in_department_schedule, is_enabled, created_at, updated_at
            FROM local_accounts
            WHERE user_id = ?
            """,
            (normalized_user_id,),
        ).fetchone()
    if not row:
        return None
    return _serialize_local_account(row)


def list_local_accounts() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, is_department_admin, show_in_department_schedule, is_enabled, created_at, updated_at
            FROM local_accounts
            ORDER BY
                CASE WHEN user_id = ? THEN 0 ELSE 1 END ASC,
                username ASC
            """,
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchall()
    return [_serialize_local_account(row) for row in rows]


def save_local_account(
    *,
    username: str,
    display_name: str,
    positions: object | None = None,
    position: str | None = None,
    department: str | None = None,
    password: str | None = None,
    enabled: bool = True,
    is_admin: bool = False,
    is_department_admin: bool = False,
    show_in_department_schedule: bool = False,
) -> dict[str, Any]:
    normalized_username = normalize_local_username(username)
    normalized_display_name = str(display_name or "").strip() or normalized_username
    raw_department = str(department or "").strip()
    if not raw_department:
        raise ValueError("请选择所属部门。")
    normalized_department = normalize_department_option_label(raw_department)
    allowed_position_options = get_local_account_position_options()["options"]
    current_department_options = get_department_options()["options"]
    if not any(item.casefold() == normalized_department.casefold() for item in current_department_options):
        save_department_options([*current_department_options, normalized_department])
    raw_positions: object = positions if positions is not None else ([position] if str(position or "").strip() else [])
    normalized_positions = normalize_user_positions(
        raw_positions,
        allow_empty=False,
        allowed_options=allowed_position_options,
    )
    normalized_position = normalized_positions[0] if normalized_positions else ""
    normalized_password = str(password or "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, is_department_admin, show_in_department_schedule, password_hash, salt_hex, iterations, is_enabled, created_at, updated_at
            FROM local_accounts
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()
        existing_user_id = str(existing["user_id"] or "") if existing else ""
        is_default_admin = (
            normalized_username == normalize_local_username(ADMIN_ACCOUNT_DEFAULT_USERNAME)
            or existing_user_id == DEFAULT_LOCAL_USER_ID
        )
        user_id = DEFAULT_LOCAL_USER_ID if is_default_admin else build_local_account_user_id(normalized_username)
        enabled_value = True if is_default_admin else bool(enabled)
        admin_value = True if is_default_admin else bool(is_admin)
        department_admin_value = False if is_default_admin else bool(is_department_admin)
        department_schedule_visible_value = bool(show_in_department_schedule)
        ensure_user(
            user_id,
            display_name=normalized_display_name,
            role="admin" if admin_value else "user",
            positions=normalized_positions,
            department=normalized_department,
        )
        if existing:
            password_hash = str(existing["password_hash"] or "")
            salt_hex = str(existing["salt_hex"] or "")
            iterations = int(existing["iterations"] or ADMIN_PASSWORD_PBKDF2_ITERATIONS)
            if normalized_password:
                credentials = make_password_credentials(normalized_username, normalized_password)
                password_hash = str(credentials["password_hash"])
                salt_hex = str(credentials["salt_hex"])
                iterations = int(credentials["iterations"])
            connection.execute(
                """
                UPDATE local_accounts
                SET user_id = ?, display_name = ?, position = ?, positions_json = ?, department = ?, is_admin = ?, is_department_admin = ?, show_in_department_schedule = ?, password_hash = ?, salt_hex = ?, iterations = ?, is_enabled = ?, updated_at = ?
                WHERE username = ?
                """,
                (
                    user_id,
                    normalized_display_name,
                    normalized_position,
                    json.dumps(normalized_positions, ensure_ascii=False),
                    normalized_department,
                    1 if admin_value else 0,
                    1 if department_admin_value else 0,
                    1 if department_schedule_visible_value else 0,
                    password_hash,
                    salt_hex,
                    iterations,
                    1 if enabled_value else 0,
                    timestamp,
                    normalized_username,
                ),
            )
        else:
            if not normalized_password:
                raise ValueError("新建本地账号时必须填写密码。")
            credentials = make_password_credentials(normalized_username, normalized_password)
            connection.execute(
                """
                INSERT INTO local_accounts (
                    username, user_id, display_name, position, positions_json, department, is_admin, is_department_admin, show_in_department_schedule, password_hash, salt_hex, iterations, is_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_username,
                    user_id,
                    normalized_display_name,
                    normalized_position,
                    json.dumps(normalized_positions, ensure_ascii=False),
                    normalized_department,
                    1 if admin_value else 0,
                    1 if department_admin_value else 0,
                    1 if department_schedule_visible_value else 0,
                    str(credentials["password_hash"]),
                    str(credentials["salt_hex"]),
                    int(credentials["iterations"]),
                    1 if enabled_value else 0,
                    timestamp,
                    timestamp,
                ),
            )
    account = get_local_account_by_username(normalized_username)
    if not account:
        raise RuntimeError("本地账号保存失败。")
    return account


def verify_local_account_password(username: str, password: str, *, require_admin: bool = False) -> dict[str, Any]:
    normalized_username = normalize_local_username(username)
    raw_password = str(password or "")
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, password_hash, salt_hex, iterations, is_enabled
            FROM local_accounts
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()
    if not row:
        raise ValueError("账号或密码错误。")
    if not bool(int(row["is_enabled"] or 0)):
        raise ValueError("该本地账号已被停用。")
    expected_hash = str(row["password_hash"] or "")
    salt_hex = str(row["salt_hex"] or "")
    iterations = int(row["iterations"] or ADMIN_PASSWORD_PBKDF2_ITERATIONS)
    actual_hash = build_password_hash(raw_password, salt_hex, iterations)
    if not expected_hash or not hmac.compare_digest(expected_hash, actual_hash):
        raise ValueError("账号或密码错误。")
    user_id = str(row["user_id"] or "")
    local_account_admin = bool(int(row["is_admin"] or 0))
    if require_admin and not has_admin_access(user_id, local_account_admin=local_account_admin):
        raise ValueError("该账号不是管理员账号。")
    user_role = "admin" if has_admin_access(user_id, local_account_admin=local_account_admin) else "user"
    stored_display_name = str(row["display_name"] or "").strip()
    stored_positions = parse_stored_positions(row["positions_json"], row["position"])
    stored_department = str(row["department"] or "").strip()
    if stored_display_name:
        ensure_user(
            user_id,
            display_name=stored_display_name,
            role=user_role,
            positions=stored_positions,
            department=stored_department,
        )
    else:
        ensure_user(user_id, role=user_role, positions=stored_positions, department=stored_department)
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("本地账号绑定的用户不存在。")
    return user


def update_local_account_password(user_id: str, current_password: str, new_password: str) -> dict[str, Any]:
    normalized_user_id = normalize_user_id(user_id)
    raw_current_password = str(current_password or "")
    raw_new_password = str(new_password or "")
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username, user_id, display_name, position, positions_json, department, is_admin, password_hash, salt_hex, iterations, is_enabled
            FROM local_accounts
            WHERE user_id = ?
            """,
            (normalized_user_id,),
        ).fetchone()
    if not row:
        raise ValueError("当前账号不是本地账号，暂不支持修改密码。")
    if not bool(int(row["is_enabled"] or 0)):
        raise ValueError("该本地账号已被停用。")
    expected_hash = str(row["password_hash"] or "")
    salt_hex = str(row["salt_hex"] or "")
    iterations = int(row["iterations"] or ADMIN_PASSWORD_PBKDF2_ITERATIONS)
    actual_hash = build_password_hash(raw_current_password, salt_hex, iterations)
    if not expected_hash or not hmac.compare_digest(expected_hash, actual_hash):
        raise ValueError("当前密码不正确。")

    credentials = make_password_credentials(str(row["username"] or ""), raw_new_password)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE local_accounts
            SET password_hash = ?, salt_hex = ?, iterations = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (
                str(credentials["password_hash"]),
                str(credentials["salt_hex"]),
                int(credentials["iterations"]),
                timestamp,
                normalized_user_id,
            ),
        )
    local_account_admin = bool(int(row["is_admin"] or 0))
    user_role = "admin" if has_admin_access(normalized_user_id, local_account_admin=local_account_admin) else "user"
    stored_display_name = str(row["display_name"] or "").strip()
    stored_positions = parse_stored_positions(row["positions_json"], row["position"])
    stored_department = str(row["department"] or "").strip()
    if stored_display_name:
        ensure_user(
            normalized_user_id,
            display_name=stored_display_name,
            role=user_role,
            positions=stored_positions,
            department=stored_department,
        )
    else:
        ensure_user(
            normalized_user_id,
            role=user_role,
            positions=stored_positions,
            department=stored_department,
        )
    account = get_local_account_by_user_id(normalized_user_id)
    if not account:
        raise RuntimeError("密码更新成功，但读取本地账号信息失败。")
    return account


def save_admin_account_credentials(username: str, password: str) -> tuple[dict[str, Any], str]:
    normalized_username = normalize_local_username(username or ADMIN_ACCOUNT_DEFAULT_USERNAME)
    normalized_password = str(password or "")
    if not normalized_password:
        raise ValueError("新密码不能为空。")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    credentials = make_password_credentials(normalized_username, normalized_password)
    preferred_positions = get_local_account_position_options()["options"][:1] or [DEFAULT_LOCAL_ACCOUNT_POSITION]
    ensure_user(
        DEFAULT_LOCAL_USER_ID,
        DEFAULT_LOCAL_USER_NAME,
        role="admin",
        positions=preferred_positions,
    )
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT username, created_at, position, positions_json
            FROM local_accounts
            WHERE user_id = ?
            """,
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
        conflict = connection.execute(
            """
            SELECT user_id
            FROM local_accounts
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()
        if conflict and str(conflict["user_id"] or "") != DEFAULT_LOCAL_USER_ID:
            raise ValueError("该账号名已被其他本地账号占用。")
        if existing:
            stored_positions = parse_stored_positions(existing["positions_json"], existing["position"]) or preferred_positions
            connection.execute(
                """
                UPDATE local_accounts
                SET username = ?, display_name = ?, position = ?, positions_json = ?, is_admin = 1, password_hash = ?, salt_hex = ?, iterations = ?, is_enabled = 1, updated_at = ?
                WHERE user_id = ?
                """,
                (
                    normalized_username,
                    DEFAULT_LOCAL_USER_NAME,
                    stored_positions[0] if stored_positions else "",
                    json.dumps(stored_positions, ensure_ascii=False),
                    str(credentials["password_hash"]),
                    str(credentials["salt_hex"]),
                    int(credentials["iterations"]),
                    timestamp,
                    DEFAULT_LOCAL_USER_ID,
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO local_accounts (
                    username, user_id, display_name, position, positions_json, is_admin, password_hash, salt_hex, iterations, is_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, 1, ?, ?)
                """,
                (
                    normalized_username,
                    DEFAULT_LOCAL_USER_ID,
                    DEFAULT_LOCAL_USER_NAME,
                    preferred_positions[0] if preferred_positions else "",
                    json.dumps(preferred_positions, ensure_ascii=False),
                    str(credentials["password_hash"]),
                    str(credentials["salt_hex"]),
                    int(credentials["iterations"]),
                    timestamp,
                    timestamp,
                ),
            )
    account = get_admin_account_public_info()
    return {
        "username": str(account.get("username") or normalized_username),
        "user_id": DEFAULT_LOCAL_USER_ID,
        "display_name": DEFAULT_LOCAL_USER_NAME,
    }, timestamp


def verify_admin_account_password(username: str, password: str) -> bool:
    try:
        verify_local_account_password(username, password, require_admin=True)
    except ValueError:
        return False
    return True


def get_admin_account_public_info() -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username
            FROM local_accounts
            WHERE user_id = ?
            """,
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
    if row:
        return {"username": str(row["username"] or ADMIN_ACCOUNT_DEFAULT_USERNAME)}
    return {"username": ADMIN_ACCOUNT_DEFAULT_USERNAME}


def get_admin_account_credentials() -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT username, salt_hex, iterations, password_hash
            FROM local_accounts
            WHERE user_id = ?
            """,
            (DEFAULT_LOCAL_USER_ID,),
        ).fetchone()
    if not row:
        return {
            "username": ADMIN_ACCOUNT_DEFAULT_USERNAME,
            "salt_hex": "",
            "iterations": ADMIN_PASSWORD_PBKDF2_ITERATIONS,
            "password_hash": "",
        }
    return {
        "username": str(row["username"] or ADMIN_ACCOUNT_DEFAULT_USERNAME),
        "salt_hex": str(row["salt_hex"] or ""),
        "iterations": int(row["iterations"] or ADMIN_PASSWORD_PBKDF2_ITERATIONS),
        "password_hash": str(row["password_hash"] or ""),
    }


def ensure_default_admin_account_credentials() -> dict[str, Any]:
    init_auth_storage()
    return get_admin_account_credentials()


def create_user_session(user_id: str) -> tuple[str, str]:
    normalized_user_id = ensure_user(normalize_user_id(user_id))
    session_token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=SESSION_DURATION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_sessions (session_token, user_id, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_token, normalized_user_id, expires_at, timestamp, timestamp),
        )
    return session_token, expires_at


def delete_user_session(session_token: str) -> bool:
    normalized_token = str(session_token or "").strip()
    if not normalized_token:
        return False
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM user_sessions WHERE session_token = ?", (normalized_token,))
    return cursor.rowcount > 0


def get_user_by_session(session_token: str | None) -> dict[str, Any] | None:
    normalized_token = str(session_token or "").strip()
    if not normalized_token:
        return None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT session_token, user_id, expires_at
            FROM user_sessions
            WHERE session_token = ?
            """,
            (normalized_token,),
        ).fetchone()
        if not row:
            return None
        if str(row["expires_at"] or "") <= timestamp:
            connection.execute("DELETE FROM user_sessions WHERE session_token = ?", (normalized_token,))
            return None
    return get_user_by_id(str(row["user_id"] or ""))


def normalize_external_base_url(value: object) -> str:
    raw_value = str(value or "").strip().rstrip("/")
    if not raw_value:
        return ""
    parsed = urlparse(raw_value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("回调基地址必须是 http:// 或 https:// 开头的完整地址。")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("回调基地址只需要填写协议、域名和端口，不要带路径或参数。")
    return f"{parsed.scheme}://{parsed.netloc}"


def build_request_origin_from_headers(headers: Any) -> str:
    forwarded_proto = str(headers.get("X-Forwarded-Proto", "") or "").split(",")[0].strip()
    forwarded_host = str(headers.get("X-Forwarded-Host", "") or "").split(",")[0].strip()
    host = forwarded_host or str(headers.get("Host", "") or "").strip()
    if not host:
        host = "127.0.0.1"
    scheme = forwarded_proto or ("https" if str(headers.get("X-Forwarded-Ssl", "") or "").lower() == "on" else "http")
    try:
        return normalize_external_base_url(f"{scheme}://{host}")
    except ValueError:
        return f"{scheme}://{host}".rstrip("/")


def normalize_dingtalk_oauth_config(payload: dict | None) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    enabled = bool(source.get("enabled"))
    allow_org_auto_login = True if source.get("allow_org_auto_login") is None else bool(source.get("allow_org_auto_login"))
    client_id = str(source.get("client_id", source.get("app_key", ""))).strip()
    client_secret = str(source.get("client_secret", source.get("app_secret", ""))).strip()
    corp_id = str(source.get("corp_id", source.get("corpId", ""))).strip()
    redirect_base_url = normalize_external_base_url(source.get("redirect_base_url", ""))
    return {
        "enabled": enabled,
        "allow_org_auto_login": allow_org_auto_login,
        "client_id": client_id,
        "client_secret": client_secret,
        "corp_id": corp_id,
        "redirect_base_url": redirect_base_url,
        "scope": DINGTALK_OAUTH_DEFAULT_SCOPE,
        "callback_path": "/api/auth/dingtalk/callback",
        "configured": bool(client_id and client_secret),
        "scan_qr_supported": False,
    }


def build_dingtalk_oauth_public_config(config: dict[str, Any], preferred_origin: str = "") -> dict[str, Any]:
    normalized_origin = ""
    try:
        normalized_origin = normalize_external_base_url(preferred_origin)
    except ValueError:
        normalized_origin = ""
    effective_base_url = config.get("redirect_base_url", "") or normalized_origin
    callback_url = f"{effective_base_url}{config['callback_path']}" if effective_base_url else ""
    return {
        "enabled": bool(config.get("enabled")),
        "configured": bool(config.get("configured")),
        "allow_org_auto_login": bool(config.get("allow_org_auto_login")),
        "corp_id": str(config.get("corp_id", "")).strip(),
        "redirect_base_url": str(config.get("redirect_base_url", "")).strip(),
        "effective_redirect_base_url": effective_base_url,
        "callback_path": str(config.get("callback_path", "")).strip(),
        "callback_url": callback_url,
        "scope": str(config.get("scope", DINGTALK_OAUTH_DEFAULT_SCOPE)).strip(),
        "scan_qr_supported": bool(config.get("scan_qr_supported")),
    }


def get_dingtalk_oauth_config() -> dict[str, Any]:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        row = connection.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key = ?",
            (DINGTALK_OAUTH_CONFIG_SETTING_KEY,),
        ).fetchone()
    loaded: dict[str, Any] = dict(DEFAULT_DINGTALK_OAUTH_CONFIG)
    if row:
        try:
            payload = json.loads(row["setting_value"] or "{}")
            if isinstance(payload, dict):
                loaded = payload
        except json.JSONDecodeError:
            loaded = {}
    return normalize_dingtalk_oauth_config(loaded)


def get_dingtalk_oauth_config_with_updated_at() -> tuple[dict[str, Any], str]:
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            (DINGTALK_OAUTH_CONFIG_SETTING_KEY,),
        ).fetchone()
    loaded: dict[str, Any] = dict(DEFAULT_DINGTALK_OAUTH_CONFIG)
    updated_at = ""
    if row:
        try:
            payload = json.loads(row["setting_value"] or "{}")
            if isinstance(payload, dict):
                loaded = payload
        except json.JSONDecodeError:
            loaded = {}
        updated_at = str(row["updated_at"] or "")
    return normalize_dingtalk_oauth_config(loaded), updated_at


def save_dingtalk_oauth_config(payload: dict | None) -> tuple[dict[str, Any], str]:
    config = normalize_dingtalk_oauth_config(payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stored_payload = {
        "enabled": config["enabled"],
        "allow_org_auto_login": config["allow_org_auto_login"],
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "corp_id": config["corp_id"],
        "redirect_base_url": config["redirect_base_url"],
    }
    with get_connection() as connection:
        _ensure_app_settings_table(connection)
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            (
                DINGTALK_OAUTH_CONFIG_SETTING_KEY,
                json.dumps(stored_payload, ensure_ascii=False),
                timestamp,
            ),
        )
    return config, timestamp


def normalize_dingtalk_login_session_id(value: object) -> str:
    session_id = str(value or "").strip()
    if not session_id or not re.fullmatch(r"[A-Za-z0-9_-]{12,128}", session_id):
        raise ValueError("扫码登录会话标识无效。")
    return session_id


def purge_expired_dingtalk_scan_login_sessions() -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute("DELETE FROM dingtalk_scan_login_sessions WHERE expires_at <= ?", (timestamp,))


def create_dingtalk_scan_login_session(redirect_base_url: str) -> dict[str, Any]:
    normalized_base_url = normalize_external_base_url(redirect_base_url)
    login_id = secrets.token_urlsafe(18)
    state_token = secrets.token_urlsafe(24)
    created_at = datetime.now()
    expires_at = created_at + timedelta(minutes=DINGTALK_SCAN_SESSION_TTL_MINUTES)
    created_at_text = created_at.strftime("%Y-%m-%d %H:%M:%S")
    expires_at_text = expires_at.strftime("%Y-%m-%d %H:%M:%S")
    purge_expired_dingtalk_scan_login_sessions()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dingtalk_scan_login_sessions (
                login_id, state_token, status, redirect_base_url, auth_user_id,
                auth_display_name, auth_raw_json, error_message, created_at, updated_at, expires_at
            )
            VALUES (?, ?, 'pending', ?, '', '', '{}', '', ?, ?, ?)
            """,
            (
                login_id,
                state_token,
                normalized_base_url,
                created_at_text,
                created_at_text,
                expires_at_text,
            ),
        )
    return {
        "login_id": login_id,
        "state_token": state_token,
        "redirect_base_url": normalized_base_url,
        "created_at": created_at_text,
        "updated_at": created_at_text,
        "expires_at": expires_at_text,
        "status": "pending",
        "auth_user_id": "",
        "auth_display_name": "",
        "auth_raw": {},
        "error_message": "",
    }


def _row_to_dingtalk_scan_session(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    try:
        auth_raw = json.loads(row["auth_raw_json"] or "{}")
    except json.JSONDecodeError:
        auth_raw = {}
    return {
        "login_id": str(row["login_id"] or ""),
        "state_token": str(row["state_token"] or ""),
        "status": str(row["status"] or "pending"),
        "redirect_base_url": str(row["redirect_base_url"] or ""),
        "auth_user_id": str(row["auth_user_id"] or ""),
        "auth_display_name": str(row["auth_display_name"] or ""),
        "auth_raw": auth_raw if isinstance(auth_raw, dict) else {},
        "error_message": str(row["error_message"] or ""),
        "created_at": str(row["created_at"] or ""),
        "updated_at": str(row["updated_at"] or ""),
        "expires_at": str(row["expires_at"] or ""),
    }


def get_dingtalk_scan_login_session(*, login_id: str | None = None, state_token: str | None = None) -> dict[str, Any] | None:
    purge_expired_dingtalk_scan_login_sessions()
    if login_id:
        normalized_login_id = normalize_dingtalk_login_session_id(login_id)
        query = "SELECT * FROM dingtalk_scan_login_sessions WHERE login_id = ?"
        params = (normalized_login_id,)
    else:
        normalized_state_token = normalize_dingtalk_login_session_id(state_token)
        query = "SELECT * FROM dingtalk_scan_login_sessions WHERE state_token = ?"
        params = (normalized_state_token,)
    with get_connection() as connection:
        row = connection.execute(query, params).fetchone()
    return _row_to_dingtalk_scan_session(row)


def update_dingtalk_scan_login_session(
    login_id: str,
    *,
    status: str,
    auth_user_id: str = "",
    auth_display_name: str = "",
    auth_payload: dict[str, Any] | None = None,
    error_message: str = "",
) -> dict[str, Any]:
    normalized_login_id = normalize_dingtalk_login_session_id(login_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE dingtalk_scan_login_sessions
            SET status = ?, auth_user_id = ?, auth_display_name = ?, auth_raw_json = ?, error_message = ?, updated_at = ?
            WHERE login_id = ?
            """,
            (
                status,
                str(auth_user_id or "").strip(),
                str(auth_display_name or "").strip(),
                json.dumps(auth_payload or {}, ensure_ascii=False),
                str(error_message or "").strip(),
                timestamp,
                normalized_login_id,
            ),
        )
    updated = get_dingtalk_scan_login_session(login_id=normalized_login_id)
    if not updated:
        raise RuntimeError("扫码登录会话不存在或已过期。")
    return updated


def build_dingtalk_oauth_callback_url(base_url: str) -> str:
    normalized_base_url = normalize_external_base_url(base_url)
    return f"{normalized_base_url}/api/auth/dingtalk/callback"


def build_dingtalk_scan_entry_url(base_url: str, login_id: str) -> str:
    normalized_base_url = normalize_external_base_url(base_url)
    normalized_login_id = normalize_dingtalk_login_session_id(login_id)
    return f"{normalized_base_url}/api/auth/dingtalk/scan-entry?{urlencode({'login_id': normalized_login_id}, quote_via=quote)}"


def build_dingtalk_oauth_authorize_url(config: dict[str, Any], login_id: str, state_token: str, redirect_base_url: str) -> str:
    if not config.get("configured"):
        raise RuntimeError("钉钉扫码登录尚未完成配置。")
    query = urlencode(
        {
            "redirect_uri": build_dingtalk_oauth_callback_url(redirect_base_url),
            "response_type": "code",
            "client_id": str(config.get("client_id", "")).strip(),
            "scope": str(config.get("scope", DINGTALK_OAUTH_DEFAULT_SCOPE)).strip(),
            "state": normalize_dingtalk_login_session_id(state_token),
            "prompt": "consent",
        },
        quote_via=quote,
    )
    return f"{DINGTALK_OAUTH_AUTHORIZE_URL}?{query}"


def extract_http_error_message(payload: object, fallback: str) -> str:
    if isinstance(payload, dict):
        for key in ("message", "msg", "error_description", "error", "errmsg", "errMsg"):
            value = str(payload.get(key, "")).strip()
            if value:
                return value
    return fallback


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    body = None
    request_headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    for key, value in (headers or {}).items():
        request_headers[str(key)] = str(value)
    request = Request(url, data=body, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        raw_body = error.read().decode("utf-8", errors="replace")
        try:
            parsed_payload = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            parsed_payload = {}
        raise RuntimeError(extract_http_error_message(parsed_payload, f"钉钉接口调用失败（HTTP {error.code}）。")) from error
    except URLError as error:
        raise RuntimeError("无法连接钉钉接口，请检查网络或钉钉开放平台配置。") from error
    try:
        data = json.loads(response_body or "{}")
    except json.JSONDecodeError as error:
        raise RuntimeError("钉钉接口返回了无法解析的 JSON。") from error
    if not isinstance(data, dict):
        raise RuntimeError("钉钉接口返回格式不正确。")
    return data


def exchange_dingtalk_user_access_token(config: dict[str, Any], auth_code: str) -> dict[str, Any]:
    payload = request_json(
        DINGTALK_OAUTH_USER_ACCESS_TOKEN_URL,
        method="POST",
        payload={
            "clientId": str(config.get("client_id", "")).strip(),
            "clientSecret": str(config.get("client_secret", "")).strip(),
            "code": str(auth_code or "").strip(),
            "grantType": "authorization_code",
        },
    )
    access_token = str(payload.get("accessToken") or payload.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError(extract_http_error_message(payload, "钉钉未返回用户 access token。"))
    return payload


def fetch_dingtalk_current_user(access_token: str) -> dict[str, Any]:
    payload = request_json(
        DINGTALK_OAUTH_USER_ME_URL,
        headers={"x-acs-dingtalk-access-token": str(access_token or "").strip()},
    )
    if not payload:
        raise RuntimeError("钉钉未返回当前登录用户信息。")
    return payload


def build_dingtalk_local_user_id(corp_id: str, union_id: str, open_id: str) -> str:
    identity_value = str(union_id or open_id or "").strip()
    if not identity_value:
        raise ValueError("钉钉未返回可识别的用户标识。")
    digest = hashlib.sha256(f"{corp_id}\u0000{identity_value}".encode("utf-8")).hexdigest()[:24]
    return f"dtu:{digest}"


def save_dingtalk_identity(corp_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    resolved_corp_id = str(corp_id or payload.get("corpId") or payload.get("corp_id") or "").strip()
    union_id = str(payload.get("unionId") or payload.get("union_id") or "").strip()
    open_id = str(payload.get("openId") or payload.get("open_id") or "").strip()
    nick = str(payload.get("nick") or payload.get("name") or "").strip()
    avatar_url = str(payload.get("avatarUrl") or payload.get("avatar_url") or "").strip()
    mobile = str(payload.get("mobile") or "").strip()
    local_user_id = build_dingtalk_local_user_id(resolved_corp_id, union_id, open_id)
    display_name = nick or mobile or local_user_id
    ensure_user(local_user_id, display_name=display_name, role="admin" if has_admin_access(local_user_id) else "user")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO dingtalk_user_identities (
                local_user_id, corp_id, union_id, open_id, nick, avatar_url, mobile, raw_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(local_user_id) DO UPDATE SET
                corp_id = excluded.corp_id,
                union_id = excluded.union_id,
                open_id = excluded.open_id,
                nick = excluded.nick,
                avatar_url = excluded.avatar_url,
                mobile = excluded.mobile,
                raw_json = excluded.raw_json,
                updated_at = excluded.updated_at
            """,
            (
                local_user_id,
                resolved_corp_id,
                union_id,
                open_id,
                nick,
                avatar_url,
                mobile,
                json.dumps(payload, ensure_ascii=False),
                timestamp,
                timestamp,
            ),
        )
    user = get_user_by_id(local_user_id)
    if user:
        return user
    return {
        "user_id": local_user_id,
        "display_name": display_name,
        "role": "admin" if has_admin_access(local_user_id) else "user",
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def list_dingtalk_user_identities(limit: int = 120) -> list[dict[str, Any]]:
    normalized_limit = max(1, min(int(limit), 300))
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                i.local_user_id,
                i.corp_id,
                i.union_id,
                i.open_id,
                i.nick,
                i.avatar_url,
                i.mobile,
                i.created_at,
                i.updated_at,
                u.display_name
            FROM dingtalk_user_identities AS i
            LEFT JOIN users AS u ON u.user_id = i.local_user_id
            ORDER BY i.updated_at DESC, i.local_user_id ASC
            LIMIT ?
            """,
            (normalized_limit,),
        ).fetchall()
    identities: list[dict[str, Any]] = []
    for row in rows:
        local_user_id = str(row["local_user_id"] or "")
        identities.append(
            {
                "local_user_id": local_user_id,
                "display_name": str(row["display_name"] or row["nick"] or local_user_id),
                "nick": str(row["nick"] or ""),
                "corp_id": str(row["corp_id"] or ""),
                "union_id": str(row["union_id"] or ""),
                "open_id": str(row["open_id"] or ""),
                "mobile": str(row["mobile"] or ""),
                "avatar_url": str(row["avatar_url"] or ""),
                "role": "admin" if has_admin_access(local_user_id) else "user",
                "created_at": str(row["created_at"] or ""),
                "updated_at": str(row["updated_at"] or ""),
            }
        )
    return identities


def resolve_dingtalk_scan_login_user(config: dict[str, Any], auth_code: str) -> tuple[dict[str, Any], dict[str, Any]]:
    token_payload = exchange_dingtalk_user_access_token(config, auth_code)
    access_token = str(token_payload.get("accessToken") or token_payload.get("access_token") or "").strip()
    corp_id = str(token_payload.get("corpId") or token_payload.get("corp_id") or config.get("corp_id") or "").strip()
    user_payload = fetch_dingtalk_current_user(access_token)
    if config.get("corp_id") and corp_id and str(config["corp_id"]).strip() != corp_id:
        raise PermissionError("扫码登录的钉钉组织与管理员配置的 CorpId 不一致。")
    merged_payload = dict(user_payload)
    if corp_id:
        merged_payload["corpId"] = corp_id
    merged_payload["source"] = "dingtalk_oauth"
    user = save_dingtalk_identity(corp_id, merged_payload)
    if config.get("allow_org_auto_login"):
        return user, merged_payload
    if not is_user_allowed_to_login(user["user_id"]):
        raise PermissionError("该钉钉账号尚未加入允许登录名单，请联系管理员放行。")
    return user, merged_payload


def build_dingtalk_callback_result_html(title: str, message: str, *, is_error: bool = False) -> str:
    safe_title = escape(title or ("登录失败" if is_error else "登录成功"))
    safe_message = escape(message or "")
    accent = "#c84a55" if is_error else "#257a55"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 20px;
      background: linear-gradient(180deg, #eef5ff, #dfeafb);
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      color: #193657;
    }}
    .card {{
      width: min(560px, 100%);
      padding: 24px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.96);
      box-shadow: 0 22px 50px rgba(28, 66, 116, 0.14);
    }}
    h1 {{ margin: 0 0 10px; font-size: 24px; color: {accent}; }}
    p {{ margin: 0; line-height: 1.7; white-space: pre-wrap; }}
    .actions {{ margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; }}
    button, a {{
      border: 1px solid #2e77d0;
      border-radius: 10px;
      background: #2e77d0;
      color: #fff;
      padding: 10px 14px;
      text-decoration: none;
      cursor: pointer;
      font: inherit;
    }}
    a.secondary, button.secondary {{
      background: #fff;
      color: #2e77d0;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{safe_title}</h1>
    <p>{safe_message}</p>
    <div class="actions">
      <button onclick="window.close()">关闭窗口</button>
      <a class="secondary" href="/">返回首页</a>
    </div>
  </div>
</body>
</html>"""
