from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # SQLAlchemy Database URL for MySQL
    sqlalchemy_database_uri: str = Field(
        default="mysql+pymysql://test_user:test_password@localhost:3306/vx_knowledge",
        alias="SQLALCHEMY_DATABASE_URI"
    )

    # Milvus settings
    milvus_uri: str = Field(default="http://localhost:19530", alias="MILVUS_URI")
    milvus_token: str = Field(default="", alias="MILVUS_TOKEN")

    # Neo4j settings
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="neo4j_password", alias="NEO4J_PASSWORD")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

settings = Settings()
