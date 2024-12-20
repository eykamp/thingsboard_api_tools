from typing import  Union, Iterable, Dict, Any, cast

try:
    from .TbModel import Attributes
    from .TbApi import TbApi
except (ModuleNotFoundError, ImportError):
    from TbModel import Attributes
    from TbApi import TbApi


class HasAttributes():
    """ Mixin class to support all attribute methods. """

    tbapi: TbApi        # Provide elsewhere


    def set_server_attributes(self, attributes: Attributes | dict[str, Any]):
        """
        Posts the attributes provided (use dict format) to the server in the Server scope
        """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)


        self._set_attributes(attributes, Attributes.Scope.SERVER)


    def get_server_attributes(self) -> Attributes:
        """ Returns a list of the device's attributes in a the Server scope. """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)


        return self._get_attributes(Attributes.Scope.SERVER)


    def delete_server_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._delete_attributes(attributes, Attributes.Scope.SERVER)


    def delete_attributes(self, attributes: Union[str, Iterable[str]], scope: Attributes.Scope) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._delete_attributes(attributes, scope)


    # Get attributes from the server
    def get_shared_attributes(self) -> Attributes:
        """ Returns a list of the device's attributes in a the Shared scope. """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._get_attributes(Attributes.Scope.SHARED)


    # Set attributes on the server
    def set_shared_attributes(self, attributes: Union[Attributes, Dict[str, Any]]):
        """
        Posts the attributes provided (use dict format) to the server in the Shared scope
        """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        self._set_attributes(attributes, Attributes.Scope.SHARED)


    # Delete attributes from the server
    def delete_shared_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._delete_attributes(attributes, Attributes.Scope.SHARED)


    def get_client_attributes(self) -> Attributes:
        """ Returns a list of the device's attributes in a the Client scope. """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._get_attributes(Attributes.Scope.CLIENT)


    def delete_client_attributes(self, attributes: Union[str, Iterable[str]]) -> bool:
        """ Pass an attribute name or a list of attributes to be deleted from the specified scope """
        try:
            from .TbModel import TbObject
        except ModuleNotFoundError:
            from TbModel import TbObject

        assert isinstance(self, TbObject)

        return self._delete_attributes(attributes, Attributes.Scope.CLIENT)


    def _set_attributes(self, attributes: Union["Attributes", Dict[str, Any]], scope: Attributes.Scope):
        """ Posts the attributes provided (use dict format) to the server at a specified scope """
        try:
            from .TbModel import Id
        except ModuleNotFoundError:
            from TbModel import Id

        if isinstance(attributes, Attributes):
            attributes = attributes.as_dict()

        id: Id = cast(Id, self.id)        # type: ignore

        url = f"/api/plugins/telemetry/{id.entity_type}/{id.id}/{scope.value}"
        return self.tbapi.post(url, attributes, f"Error setting {scope.value} attributes for '{id}'")


    def _get_attributes(self, scope: Attributes.Scope):
        """
        Returns a list of the device's attributes in the specified scope.
        Looks like [{'key': 'active', 'lastUpdateTs': 1595969455329, 'value': False}, ...]
        """
        try:
            from .TbModel import Id
        except ModuleNotFoundError:
            from TbModel import Id

        id: Id = cast(Id, self.id)        # type: ignore

        url = f"/api/plugins/telemetry/{id.entity_type}/{id.id}/values/attributes/{scope.value}"
        attribute_data = self.tbapi.get(url, f"Error retrieving {scope.value} attributes for '{id}'")

        return Attributes(attribute_data, scope)


    def _delete_attributes(self, attributes: str | Iterable[str], scope: Attributes.Scope) -> bool:
        """
        Pass an attribute name or a list of attributes to be deleted from the specified scope;
        returns True if operation generally, succeeded, even if attribute we're deleting didn't
        exist.
        """
        try:
            from .TbModel import Id
        except ModuleNotFoundError:
            from TbModel import Id

        id: Id = cast(Id, self.id)        # type: ignore

        if not isinstance(attributes, str):
            attributes = ",".join(attributes)

        url = f"/api/plugins/telemetry/{id.entity_type}/{id.id}/{scope.value}?keys={attributes}"
        return self.tbapi.delete(url, f"Error deleting {scope.value} attributes for '{id}'")

