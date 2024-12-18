# Copyright 2018-2024, Chris Eykamp

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

from typing import  Any
from pydantic import Field
from .TbModel import TbObject, Id
from .HasAttributes import HasAttributes


class DeviceProfileInfo(TbObject, HasAttributes):
    name: str                                                   # Default appars to be "device_type"
    image: str | None
    default_dashboard_id: Id | None
    type: str | None                                            # Default appears to be "DEFAULT"
    transport_type: str = Field(alias="transportType")          # Default appears to be "DEFAULT"
    default_dashboard_id: Id | None = Field(alias="defaultDashboardId")


class DeviceProfile(DeviceProfileInfo):
    tenant_id: Id | None = Field(alias="tenantId")
    description: str                                            # Default appears to be "Default device profile"
    provision_type: str = Field(alias="provisionType")          # Default appears to be "DISABLED"
    default_queue_name: str | None = Field(alias="defaultQueueName")
    provision_device_key: str | None = Field(alias="provisionDeviceKey")
    firmware_id: Id | None = Field(alias="firmwareId")
    software_id: Id | None = Field(alias="softwareId")
    default_rule_chain_id: Id | None = Field(alias="defaultRuleChainId")
    default_queue_name: str | None = Field(alias="defaultQueueName")
    default_edge_rule_chain_id: Id | None = Field(alias="defaultEdgeRuleChainId")
    external_id: Id | None = Field(alias="externalId")
    profile_data: dict[str, Any] = Field(alias="profileData")       # TODO: Needs to be built out

# Sample profile_data from swagger docs
#   "profileData": {
#     "configuration": {},
#     "transportConfiguration": {},
#     "provisionConfiguration": {
#       "provisionDeviceSecret": "string"
#     },
#     "alarms": [
#       {
#         "id": "highTemperatureAlarmID",
#         "alarmType": "High Temperature Alarm",
#         "createRules": {
#           "additionalProp1": {
#             "condition": {
#               "condition": [
#                 {
#                   "key": {
#                     "type": "TIME_SERIES",
#                     "key": "temp"
#                   },
#                   "valueType": "NUMERIC",
#                   "value": {},
#                   "predicate": {}
#                 }
#               ],
#               "spec": {}
#             },
#             "schedule": {
#               "dynamicValue": {
#                 "inherit": true,
#                 "sourceAttribute": "string",
#                 "sourceType": "CURRENT_CUSTOMER"
#               },
#               "type": "ANY_TIME"
#             },
#             "alarmDetails": "string",
#             "dashboardId": {
#               "id": "784f394c-42b6-435a-983c-b7beff2784f9",
#               "entityType": "DASHBOARD"
#             }
#           },
#           "additionalProp2": {
#             "condition": {
#               "condition": [
#                 {
#                   "key": {
#                     "type": "TIME_SERIES",
#                     "key": "temp"
#                   },
#                   "valueType": "NUMERIC",
#                   "value": {},
#                   "predicate": {}
#                 }
#               ],
#               "spec": {}
#             },
#             "schedule": {
#               "dynamicValue": {
#                 "inherit": true,
#                 "sourceAttribute": "string",
#                 "sourceType": "CURRENT_CUSTOMER"
#               },
#               "type": "ANY_TIME"
#             },
#             "alarmDetails": "string",
#             "dashboardId": {
#               "id": "784f394c-42b6-435a-983c-b7beff2784f9",
#               "entityType": "DASHBOARD"
#             }
#           },
#           "additionalProp3": {
#             "condition": {
#               "condition": [
#                 {
#                   "key": {
#                     "type": "TIME_SERIES",
#                     "key": "temp"
#                   },
#                   "valueType": "NUMERIC",
#                   "value": {},
#                   "predicate": {}
#                 }
#               ],
#               "spec": {}
#             },
#             "schedule": {
#               "dynamicValue": {
#                 "inherit": true,
#                 "sourceAttribute": "string",
#                 "sourceType": "CURRENT_CUSTOMER"
#               },
#               "type": "ANY_TIME"
#             },
#             "alarmDetails": "string",
#             "dashboardId": {
#               "id": "784f394c-42b6-435a-983c-b7beff2784f9",
#               "entityType": "DASHBOARD"
#             }
#           }
#         },
#         "clearRule": {
#           "condition": {
#             "condition": [
#               {
#                 "key": {
#                   "type": "TIME_SERIES",
#                   "key": "temp"
#                 },
#                 "valueType": "NUMERIC",
#                 "value": {},
#                 "predicate": {}
#               }
#             ],
#             "spec": {}
#           },
#           "schedule": {
#             "dynamicValue": {
#               "inherit": true,
#               "sourceAttribute": "string",
#               "sourceType": "CURRENT_CUSTOMER"
#             },
#             "type": "ANY_TIME"
#           },
#           "alarmDetails": "string",
#           "dashboardId": {
#             "id": "784f394c-42b6-435a-983c-b7beff2784f9",
#             "entityType": "DASHBOARD"
#           }
#         },
#         "propagate": true,
#         "propagateToOwner": true,
#         "propagateToTenant": true,
#         "propagateRelationTypes": [
#           "string"
#         ]
#       }
#     ]
#   },
