from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class BotSettings(BaseSettings):
    BOT_TOKEN: str
    LLM_TOKEN: str
    MODEL_NAME: str

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env"), extra="ignore")

    def get_bot_token(self):
        return self.BOT_TOKEN
    
    def get_llm_token(self):
        return self.LLM_TOKEN
    
    def get_model_name(self):
        return self.MODEL_NAME

settings = BotSettings()