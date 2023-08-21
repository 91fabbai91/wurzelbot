from pydantic import SecretStr, BaseModel,validator, Field, PositiveInt, StrictStr

class LoginData(BaseModel):
    server: PositiveInt = Field(..., allow_mutation=False)
    username: StrictStr = Field(..., allow_mutation=False)
    password: SecretStr = Field(..., allow_mutation=False)

    class Config:
        validate_assignment = True
        frozen = True

    @validator('server')
    def server_match(cls, v):
        if v < 0 or v > 46:
            raise ValueError("Server must be Integer, greater than 0 and smaller than 47")
        return v
