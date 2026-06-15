from typing import Optional
from pydantic import BaseModel, Field, model_validator

class ExportRequest(BaseModel):
    uri: Optional[str] = None
    cluster: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    db: str = Field(..., min_length=1)
    collection: str = Field(..., min_length=1)

    @model_validator(mode="before")
    @classmethod
    def strip_whitespace(cls, values):
        if isinstance(values, dict):
            for field in ['uri', 'cluster', 'username', 'password', 'db', 'collection']:
                if field in values and isinstance(values[field], str):
                    values[field] = values[field].strip()
        return values

    @model_validator(mode="after")
    def check_credentials(self) -> "ExportRequest":
        # Si aucune URI n'est fournie, les détails du cluster sont requis
        if not self.uri:
            if not all([self.cluster, self.username, self.password]):
                raise ValueError(
                    "Vous devez fournir soit une 'URI de connexion', soit le triplet ('Cluster', 'Utilisateur', 'Mot de passe')."
                )
        return self
