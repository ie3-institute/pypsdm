from abc import abstractmethod

from pypsdm.models.input.mixins import HasTypeMixin


class SpTypeMixin(HasTypeMixin):
    @property
    def capex(self):
        return self.data["capex"]

    @property
    def opex(self):
        return self.data["opex"]

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @staticmethod
    @abstractmethod
    def entity_attributes() -> list[str]:
        pass

    @staticmethod
    def type_attributes() -> list[str]:
        return HasTypeMixin.type_attributes() + [
            "capex",
            "opex",
            "s_rated",
            "cos_phi_rated",
        ]
