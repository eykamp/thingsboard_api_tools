# Copyright 2018-2019, Chris Eykamp

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Update with: pip install git+git://github.com/eykamp/thingsboard_api_tools.git --upgrade

# pyright: strict
from datetime import datetime
from typing import  Dict, List, Any, Optional, Union, TYPE_CHECKING
from pydantic import Field
from TbModel import Id, TbObject, TbModel

if TYPE_CHECKING:
    from Customer import Customer, CustomerId
    from TbApi import TbApi

class Widget(TbModel):
    id: Union[Id, str]      # in a DashboardDef, widgets have GUIDs for ids; other times they have full-on Id objects
    is_system_type: bool = Field(alias="isSystemType")
    bundle_alias: str = Field(alias="bundleAlias")
    type_alias: str = Field(alias="typeAlias")
    type: str
    title: str
    size_x: int = Field(alias="sizeX")
    size_y: int = Field(alias="sizeY")
    config: Dict[str, Any]
    # index: str        # TODO: Put in slots?

    def __str__(self) -> str:
        return f"Widget ({self.title}, {self.type})"
        # return f"Widget ({self.title}, {self.type}, {self.index})"


class SubWidget(TbModel):      # used within States <- Layouts <- Main <- Widgets
    size_x: int = Field(alias="sizeX")
    size_y: int = Field(alias="sizeY")
    mobile_height: Optional[int] = Field(alias="mobileHeight")
    row: int
    col: int
    # index: str        # TODO: Put in slots?

    def __str__(self) -> str:
        return f"SubWidget"
        return f"SubWidget ({self.index})"


class GridSetting(TbModel):        # used within States <- Layouts <- Main <- GridSetting
    background_color: str = Field(alias="backgroundColor")  # "#3e4b6b",
    color: str  # "rgba(1, 1, 1, 0.87)",
    columns: int
    margins: List[int]  # [10, 10],
    background_size_mode: str = Field(alias="backgroundSizeMode")  # "100%",
    auto_fill_height: bool = Field(alias="autoFillHeight")
    mobile_auto_fill_height: bool = Field(alias="mobileAutoFillHeight")
    mobile_row_height: int = Field(alias="mobileRowHeight")

    def __str__(self) -> str:
        return f"GridSetting"


class Layout(TbModel):      # used within States <- Layouts <- Main <- Widgets
    widgets: Dict[str, SubWidget]
    grid_settings: GridSetting = Field(alias="gridSettings")
    # index: str          # new name of the layout

    def __str__(self) -> str:
        return f"Layout ({len(self.widgets)})"


class State(TbModel):      # referred to in "default", the only object nested inside of States
    name: str
    root: bool
    layouts: Dict[str, Layout]
    # widgets: list   # skipping the step of going through widgets, this is the same as self.layouts["main"].widgets
    # index: str    # TODO: Put in slots?

    def __str__(self) -> str:
        return f"State ({self.name})"
        # return f"State ({self.index} {self.name})"


class Filter(TbModel):
    type: Optional[str]
    resolve_multiple: Optional[bool] = Field(alias="resolveMultiple")
    single_entity: Optional[Id] = Field(alias="singleEntity")
    entity_type: Optional[str] = Field(alias="entityType")
    entity_name_filter: Optional[str] = Field(alias="entityNameFilter")

    def __str__(self) -> str:
        return f"Filter ({self.type}, {self.single_entity.id if self.single_entity else 'Undefined ID'})"


class EntityAlias(TbModel):
    id: str
    alias: str
    filter: Filter

    # index: str

    def __str__(self) -> str:
        return f"Entity Alias ({self.alias}, {self.id})"


class Setting(TbModel):
    state_controller_id: str = Field(alias="stateControllerId")
    show_title: bool = Field(alias="showTitle")
    show_dashboards_select: bool = Field(alias="showDashboardsSelect")
    show_entities_select: bool = Field(alias="showEntitiesSelect")
    show_dashboard_timewindow: bool = Field(alias="showDashboardTimewindow")
    show_dashboard_export: bool = Field(alias="showDashboardExport")
    toolbar_always_open: bool = Field(alias="toolbarAlwaysOpen")
    title_color: str = Field(alias="titleColor")

    def __str__(self) -> str:
        return f"Settings ({self.dict()})"


class RealTime(TbModel):
    interval: int
    time_window_ms: int = Field(alias="timewindowMs")

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Aggregation(TbModel):
    type: str
    limit: int

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class TimeWindow(TbModel):
    real_time: RealTime = Field(alias="realtime")
    aggregation: Aggregation

    def __str__(self) -> str:
        return f"Timewindow ({self.dict()})"


class Configuration(TbModel):
    widgets: Dict[str, Widget]
    states: Dict[str, State]
    entity_aliases: Dict[str, EntityAlias] = Field(alias="entityAliases")
    timewindow: TimeWindow
    settings: Setting
    # name: str

    def __str__(self) -> str:
        return f"Configuration"


class Dashboard(TbObject):
    from Customer import CustomerId

    id: Id
    created_time: datetime = Field(alias="createdTime")
    tenant_id: Id = Field(alias="tenantId")
    name: Optional[str]
    title: Optional[str]
    assigned_customers: Optional[List[CustomerId]] = Field(alias="assignedCustomers")


    def __str__(self) -> str:
        return f"Dashboard ({self.name}, {self.title}, {self.id.id})"


    def is_public(self) -> bool:
        """
        Return True if dashboard is owned by the public user False otherwise
        """
        if self.assigned_customers is None:
            return False

        for c in self.assigned_customers:
            if c.public:
                return True

        return False


    def assign_to_user(self, customer: "Customer") -> Dict[str, Any]:
        """
        Returns dashboard definition
        """
        dashboard_id = self.id.id
        customer_id = customer.id.id
        return self.tbapi.post(f"/api/customer/{customer_id}/dashboard/{dashboard_id}", None, f"Could not assign dashboard '{dashboard_id}' to customer '{customer_id}'")


    # def is_public(self) -> bool:
    #     """ Return True if device is owned by the public user, False otherwise """
    #     pub_id = self.tbapi.get_public_user_id()
    #     return self.customer_id == pub_id


    def make_public(self) -> None:
        """ Assigns device to the public customer, which is how TB makes things public. """
        if not self.is_public():
            self.tbapi.post(f"/api/customer/public/dashboard/{self.id.id}", None, f"Error assigning dash '{self.id.id}' to public customer")
            # self.customer_id = Id(**obj["customerId"])
            self.assigned_customers = [self.tbapi.get_public_user_id()]


    def get_public_url(self) -> Optional[str]:
        if not self.is_public():
            return None

        dashboard_id = self.id.id
        public_id = self.tbapi.get_public_user_id().id.id

        return f"{self.tbapi.mothership_url}/dashboard/{dashboard_id}?publicId={public_id}"


    def get_definition(self) -> "DashboardDef":
        dash_id = self.id.id
        obj = self.tbapi.get(f"/api/dashboard/{dash_id}", f"Error retrieving dashboard definition for '{dash_id}'")
        return DashboardDef(self.tbapi, **obj)


    def delete(self) -> bool:
        """
        Returns True if dashboard was deleted, False if it did not exist
        """
        dashboard_id = self.id.id
        return self.tbapi.delete(f"/api/dashboard/{dashboard_id}", f"Error deleting dashboard '{dashboard_id}'")


class DashboardDef(Dashboard):
    """ Extends Dashboard by adding a configuration. """
    configuration: Configuration

    def __str__(self) -> str:
        return f"Dashboard Definition ({self.name}, {self.title}, {self.id.id})"


    def delete_server_attributes(self):
        """
        Saves a fully formed dashboard definition
        """
        return self.tbapi.post("/api/dashboard", self.json(by_alias=True), "Error saving dashboard")

