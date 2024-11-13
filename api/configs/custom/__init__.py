from pydantic import Field
from pydantic_settings import BaseSettings

class UserAccountDefaultConfig(BaseSettings):
    user_account_month_before_banned: int = Field(12, title="The number of months before the user account is banned")
    user_account_max_of_apps: int = Field(10, title="The maximum number of apps that a user can create")