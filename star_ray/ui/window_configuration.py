"""Module defines a utility class `WindowConfiguration` that may be used to configure application windows."""

from pydantic import BaseModel, Field


class WindowConfiguration(BaseModel):
    """Window Configuration."""

    x: int = Field(default=0)
    y: int = Field(default=0)
    width: int = Field(default=640)
    height: int = Field(default=480)
    title: str = Field(default="window")
    resizable: bool = Field(default=False)
    fullscreen: bool = Field(default=False)
    background_color: str = "#ffffff"
