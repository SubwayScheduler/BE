from typing import List, Optional
from pydantic import BaseModel
from datetime import time
from typing import Literal

# Administrator 모델
class AdministratorBase(BaseModel):
    name: str

class AdministratorCreate(AdministratorBase):
    password: str

class AdministratorUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class AdministratorInDBBase(AdministratorBase):
    ID: int

    class Config:
        orm_mode = True

class Administrator(AdministratorInDBBase):
    pass

# Line 모델
class LineBase(BaseModel):
    route_shape: Optional[Literal['ROUND-TRIP', 'CIRCULAR']] = None

class LineCreate(LineBase):
    name: str

class LineUpdate(LineBase):
    name: Optional[str] = None
    route_shape: Optional[Literal['ROUND-TRIP', 'CIRCULAR']] = None

class LineInDBBase(LineBase):
    ID: int

    class Config:
        orm_mode = True

class Line(LineInDBBase):
    stations: List['Station'] = []
    garage: Optional['Garage'] = None
    trains: List['Train'] = []

# Station 모델
class StationBase(BaseModel):
    name: str
    line_ID: int

class StationCreate(StationBase):
    pass

class StationUpdate(BaseModel):
    name: Optional[str] = None
    line_ID: Optional[int] = None

class StationInDBBase(StationBase):
    ID: int

    class Config:
        orm_mode = True

class Station(StationInDBBase):
    platforms: List['Platform'] = []
    eta: Optional['ETA'] = None
    garage: Optional['Garage'] = None

# Platform 모델
class PlatformBase(BaseModel):
    station_ID: int
    bound_to: bool

class PlatformCreate(PlatformBase):
    pass

class PlatformUpdate(BaseModel):
    bound_to: Optional[bool] = None

class PlatformInDBBase(PlatformBase):

    class Config:
        orm_mode = True

class Platform(PlatformInDBBase):
    congestions: List['Congestion'] = []

# Congestion 모델
class CongestionBase(BaseModel):
    time_slot: time
    congest_status: Optional[float] = None

class CongestionCreate(CongestionBase):
    platform_station_ID: int
    platform_bound_to: bool

class CongestionUpdate(BaseModel):
    time_slot: Optional[time] = None
    congest_status: Optional[float] = None

class CongestionInDBBase(CongestionBase):
    platform_station_ID: int
    platform_bound_to: bool

    class Config:
        orm_mode = True

class Congestion(CongestionInDBBase):
    pass

# ETA 모델
class ETABase(BaseModel):
    station_ID: int
    ET: time

class ETACreate(ETABase):
    pass

class ETAUpdate(BaseModel):
    ET: Optional[time] = None

class ETAInDBBase(ETABase):

    class Config:
        orm_mode = True

class ETA(ETAInDBBase):
    pass

# Garage 모델
class GarageBase(BaseModel):
    line_ID: int
    station_ID: int

class GarageCreate(GarageBase):
    pass

class GarageUpdate(BaseModel):
    station_ID: Optional[int] = None

class GarageInDBBase(GarageBase):

    class Config:
        orm_mode = True

class Garage(GarageInDBBase):
    pass

# Motorman 모델
class MotormanBase(BaseModel):
    name: str

class MotormanCreate(MotormanBase):
    pass

class MotormanUpdate(MotormanBase):
    pass

class MotormanInDBBase(MotormanBase):
    ID: int

    class Config:
        orm_mode = True

class Motorman(MotormanInDBBase):
    trains: List['TrainMotorman'] = []

# Train 모델
class TrainBase(BaseModel):
    capacity: int
    Line_ID: int

class TrainCreate(TrainBase):
    pass

class TrainUpdate(BaseModel):
    capacity: Optional[int] = None
    Line_ID: Optional[int] = None

class TrainInDBBase(TrainBase):
    ID: int

    class Config:
        orm_mode = True

class Train(TrainInDBBase):
    motormen: List['TrainMotorman'] = []

# TrainMotorman 모델
class TrainMotormanBase(BaseModel):
    Train_ID: int
    Motorman_ID: int

class TrainMotormanCreate(TrainMotormanBase):
    pass

class TrainMotormanUpdate(BaseModel):
    pass

class TrainMotormanInDBBase(TrainMotormanBase):

    class Config:
        orm_mode = True

class TrainMotorman(TrainMotormanInDBBase):
    pass

# 순환 참조 해결을 위한 모델 업데이트
Line.update_forward_refs()
Station.update_forward_refs()
Platform.update_forward_refs()
Congestion.update_forward_refs()
Motorman.update_forward_refs()
Train.update_forward_refs()
