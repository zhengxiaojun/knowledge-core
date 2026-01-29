from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App settings
    project_name: str = Field(default="AI 测试用例自动生成系统", alias="PROJECT_NAME")
    project_version: str = Field(default="1.0.0", alias="PROJECT_VERSION")
    project_description: str = Field(
        default="基于向量检索、测试知识图谱和大语言模型的AI测试用例自动生成系统",
        alias="PROJECT_DESCRIPTION"
    )
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
    milvus_collection_name: str = Field(default="test_knowledge_vectors", alias="MILVUS_COLLECTION_NAME")
    embedding_dim: int = Field(default=1536, alias="EMBEDDING_DIM")

    # Neo4j settings
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="neo4j_password", alias="NEO4J_PASSWORD")

    # OpenAI settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    # LLM settings
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")

settings = Settings()
