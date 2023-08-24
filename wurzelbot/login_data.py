from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    SecretStr,
    StrictStr,
    field_validator,
)


class LoginData(BaseModel):
    server: PositiveInt = Field(..., frozen=True)
    username: StrictStr = Field(..., frozen=True)
    password: SecretStr = Field(..., frozen=True)
    model_config = ConfigDict(validate_assignment=True, frozen=True)

    @field_validator("server")
    @classmethod
    def server_match(cls, server):
        if server < 0 or server > 46:
            raise ValueError(
                "Server must be Integer, greater than 0 and smaller than 47"
            )
        return server
