from pydantic import BaseModel, Field


class WindowConfiguration(BaseModel):

    width: int = Field(default=640)
    height: int = Field(default=480)
    title: str = Field(default="window")
    resizable: bool = Field(default=False)
    fullscreen: bool = Field(default=False)
    background_color: str = "#ffffff"
