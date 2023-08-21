from pydantic import field_validator, ConfigDict, SecretStr, BaseModel,Field, PositiveInt, StrictStr

class LoginData(BaseModel):
    server: PositiveInt = Field(..., frozen=True)
    username: StrictStr = Field(..., frozen=True)
    password: SecretStr = Field(..., frozen=True)
    model_config = ConfigDict(validate_assignment=True, frozen=True)

    @field_validator('server')
    @classmethod
    def server_match(cls, v):
        if v < 0 or v > 46:
            raise ValueError("Server must be Integer, greater than 0 and smaller than 47")
        return v
