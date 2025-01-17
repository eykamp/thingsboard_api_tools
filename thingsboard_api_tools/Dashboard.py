# Copyright 2018-2024, Chris Eykamp

# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the``
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from typing import  Dict, List, Any, Optional
from pydantic import Field

from .TbModel import Id, TbObject, TbModel
from .Customer import Customer, CustomerId


class Widget(TbModel):
    id: Id | str | None = None     # in a DashboardDef, widgets have GUIDs for ids; other times they have full-on Id objects
    is_system_type: bool | None = Field(default=None, alias="isSystemType")
    bundle_alias: str | None = Field(default=None, alias="bundleAlias")
    type_alias: str | None = Field(default=None, alias="typeAlias")
    type: str
    name: str | None = Field(default=None, alias="title")
    size_x: float = Field(alias="sizeX")
    size_y: float = Field(alias="sizeY")
    config: Dict[str, Any]
    # index: str        # TODO: Put in slots?

    def __str__(self) -> str:
        return f"Widget ({self.name}, {self.type})"


class SubWidget(TbModel):      # used within States <- Layouts <- Main <- Widgets
    id: str | None = None
    type: str | None = None
    size_x: float = Field(alias="sizeX")
    size_y: float = Field(alias="sizeY")
    mobile_height: Optional[int] = Field(default=None, alias="mobileHeight")    # Sometimes missing from the TB json; default to None
    config: dict[str, Any] = {}
    row: int
    col: int
    type_full_fqn: str | None = Field(default=None, alias="typeFullFqn")

    # index: str        # TODO: Put in slots?

    def __str__(self) -> str:
        return "SubWidget"
        # return f"SubWidget ({self.index})"


class GridSetting(TbModel):        # used within States <- Layouts <- Main <- GridSetting
    background_color: str = Field(alias="backgroundColor")  # "#3e4b6b",
    color: str | None = None  # "rgba(1, 1, 1, 0.87)",
    columns: int
    margin: int | None = None
    margins: List[int] | None = None  # [10, 10],
    outer_margin: bool | None = Field(default=None, alias="outerMargin")
    background_size_mode: str = Field(alias="backgroundSizeMode")  # "100%",
    auto_fill_height: bool | None = Field(default=None, alias="autoFillHeight")
    mobile_auto_fill_height: bool | None = Field(default=None, alias="mobileAutoFillHeight")
    mobile_row_height: int | None = Field(default=None, alias="mobileRowHeight")

    def __str__(self) -> str:
        return "GridSetting"


class Layout(TbModel):      # used within States <- Layouts <- Main <- Widgets
    widgets: dict[str, SubWidget] | list[SubWidget]             # demo.thingsboard.io has list, Sensorbot has dict
    grid_settings: GridSetting = Field(alias="gridSettings")
    # index: str          # new name of the layout

    def __str__(self) -> str:
        return f"Layout ({len(self.widgets)} widgets)"


class State(TbModel):      # referred to in "default", the only object nested inside of States
    name: str
    root: bool
    layouts: Dict[str, Layout]
    # widgets: list   # skipping the step of going through widgets, this is the same as self.layouts["main"].widgets
    # index: str    # TODO: Put in slots?

    def __str__(self) -> str:
        return f"State ({self.name})"


class Filter(TbModel):
    type: Optional[str]
    resolve_multiple: Optional[bool] = Field(alias="resolveMultiple")
    single_entity: Optional[Id] = Field(default=None, alias="singleEntity")     # Sometimes missing from json; default to None
    entity_type: Optional[str] = Field(default=None, alias="entityType")        # Sometimes missing from json; default to None
    entity_name_filter: Optional[str] = Field(default=None, alias="entityNameFilter")

    def __str__(self) -> str:
        return f"Filter ({self.type}, {self.single_entity.id if self.single_entity else 'Undefined ID'})"


class EntityAlias(TbModel):
    id: str | None = None
    alias: str
    filter: Filter | None = None

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
    title_color: str | None = Field(default=None, alias="titleColor")

    def __str__(self) -> str:
        return f"Settings ({self.model_dump()})"


class RealTime(TbModel):
    interval: int
    time_window_ms: int = Field(alias="timewindowMs")
    realtime_type: int | None = Field(default=None, alias="realtimeType")
    quick_interval: str | None = Field(default=None, alias="quickInterval")        # e.g. "CURRENT_DAY"


    def __str__(self) -> str:
        return f"Real Time ({self.model_dump()})"


class Aggregation(TbModel):
    type: str
    limit: int

    def __str__(self) -> str:
        return f"Aggregation ({self.model_dump()})"


class FixedTimeWindow(TbModel):
    start_time_ms: int = Field(alias="startTimeMs")
    end_time_ms: int = Field(alias="endTimeMs")

    def __str__(self) -> str:
        return f"Fixed Time Window ({self.model_dump()})"


class History(TbModel):
    history_type: int = Field(alias="historyType")
    interval: int = Field(alias="interval")
    time_window_ms: int = Field(alias="timewindowMs")
    fixed_time_window: FixedTimeWindow = Field(alias="fixedTimewindow")

    def __str__(self) -> str:
        return f"History ({self.model_dump()})"


class TimeWindow(TbModel):
    display_value: str = Field(alias="displayValue")
    selected_tab: int = Field(alias="selectedTab")
    real_time: RealTime = Field(alias="realtime")
    aggregation: Aggregation
    history: History | None = None

    def __str__(self) -> str:
        return f"Time Window ({self.model_dump()})"


class Configuration(TbModel):
    description: str | None = None
    widgets: Dict[str, Widget] | List[Widget] | None = None     # demo.thingsboard.io has list, Sensorbot has dict
    states: Dict[str, State] | None = None
    device_aliases: Dict[str, EntityAlias] | None = Field(default=None, alias="deviceAliases")  # I've seen both of these
    entity_aliases: Dict[str, EntityAlias] | None = Field(default=None, alias="entityAliases")
    time_window: TimeWindow | None = Field(default=None, alias="timewindow")
    filters: dict[str, Any] = Field(default={})
    settings: Setting | None = None
    # name: str

    def __str__(self) -> str:
        return "Configuration"


class DashboardHeader(TbObject):
    """
    A Dashboard with no configuration object -- what you get from TB if you request a group of dashboards.
    """
    # id, created_time provided by TbObject
    tenant_id: Id = Field(alias="tenantId")
    name: str | None = Field(default=None, alias="title")
    assigned_customers: list[CustomerId] | None = Field(alias="assignedCustomers")
    image: str | None
    mobile_hide: bool | None = Field(default=None, alias="mobileHide")
    mobile_order: int | None = Field(default=None, alias="mobileOrder")
    external_id: Id | None = Field(default=None, alias="externalId")


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


    def assign_to(self, customer: "Customer") -> None:
        from .Customer import CustomerId

        """
        Returns dashboard definition
        """
        dashboard_id = self.id.id
        customer_id = customer.id.id
        resp = self.tbapi.post(f"/api/customer/{customer_id}/dashboard/{dashboard_id}", None, f"Could not assign dashboard '{dashboard_id}' to customer '{customer_id}'")

        # Update customer object with new assignments
        self.assigned_customers = []
        for cust_data in resp["assignedCustomers"]:
            self.assigned_customers.append(CustomerId(**cust_data))

        return resp


    def get_customers(self) -> List["Customer"]:
        """ Returns a list of all customers assigned to the device, if any. """

        custlist: List["Customer"] = []
        for custid in self.assigned_customers or []:        # Handle None
            cust = self.tbapi.get_customer_by_id(custid)
            if cust:
                custlist.append(cust)

        return custlist


    def make_public(self) -> None:
        """ Assigns dashboard  to the public customer, which is how TB makes things public. """
        if self.is_public():
            return

        self.tbapi.post(f"/api/customer/public/dashboard/{self.id.id}", None, f"Error assigning dash '{self.id.id}' to public customer")
        # self.customer_id = Id(**obj["customerId"])

        public_id = self.tbapi.get_public_user_id()
        assert public_id        # Should never because we now have something assigned to the public user
        if self.assigned_customers is None:
            self.assigned_customers = []

        self.assigned_customers.append(public_id)


    def make_private(self) -> None:
        """ Removes the public customer, which will make it visible only to assigned customers. """
        if not self.is_public():
            return

        self.tbapi.delete(f"/api/customer/public/dashboard/{self.id.id}", f"Error removing the public customer from dash '{self.id.id}'")
        # self.customer_id = Id(**obj["customerId"])

        public_id = self.tbapi.get_public_user_id()
        assert public_id                # Should never because we now have something assigned to the public user
        assert self.assigned_customers  # If we're public, we have at least one customer, so self.assigned_customers should never be empty or None
        self.assigned_customers.remove(public_id)


    def get_public_url(self) -> Optional[str]:
        if not self.is_public():
            return None

        dashboard_id = self.id.id

        public_id = self.tbapi.get_public_user_id()
        assert public_id        # Should always be true because this item is public so the public user should exist

        public_guid = public_id.id.id

        return f"{self.tbapi.mothership_url}/dashboard/{dashboard_id}?publicId={public_guid}"


    def get_dashboard(self):
        dash_id = self.id.id
        obj = self.tbapi.get(f"/api/dashboard/{dash_id}", f"Error retrieving dashboard definition for '{dash_id}'")
        return Dashboard(tbapi=self.tbapi, **obj)


    def update(self):
        """
        Writes object back to the database.  Use this if you want to save any modified properties.
        """
        return self.tbapi.post("/api/dashboard", self.model_dump_json(by_alias=True), f"Error updating '{self.id}'")


    def delete(self) -> bool:
        """
        Returns True if dashboard was deleted, False if it did not exist
        """
        dashboard_id = self.id.id
        return self.tbapi.delete(f"/api/dashboard/{dashboard_id}", f"Error deleting dashboard '{dashboard_id}'")


class Dashboard(DashboardHeader):
    """ Extends Dashboard by adding a configuration. """
    configuration: Configuration | None     # Empty dashboards will have no configuration
