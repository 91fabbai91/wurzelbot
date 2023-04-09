from pydantic import SecretStr, BaseModel,validator

class LoginData(BaseModel):
    server: int
    username: str
    password: SecretStr

    @validator('server')
    def server_match(cls, v):
        if v < 0 or v > 46:
            raise ValueError("Server must be Integer, greater than 0 and smaller than 47")
        return v
