from functools import lru_cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRIDGE_", case_sensitive=False)

    # ----- public identity -----
    public_url: HttpUrl = HttpUrl("https://bridge.vir.group")
    log_level: str = "INFO"

    # ----- Supabase project we trust JWTs from -----
    supabase_url: HttpUrl
    supabase_jwt_secret: str
    supabase_service_role: str

    # ----- Synapse homeserver we provision into -----
    synapse_internal_url: str = "http://synapse:8008"
    synapse_server_name: str = "vir.group"
    synapse_admin_token: str

    # ----- Webhook authentication for /users/sync -----
    webhook_secret: str = ""

    # ----- Defaults applied to provisioned Matrix users -----
    default_displayname_template: str = "{username}"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
