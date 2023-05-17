import logging

from odoo import api

_logger = logging.getLogger(__name__)

native_fields_to_compute = api.Environment.fields_to_compute
native_records_to_compute = api.Environment.records_to_compute

MIN_RECORDS_FOR_ASYNC_RECOMPUTE = 10
FIELD_CANARY_NAME = "force_recompute_canary"


# Those methods are overwriting the odoo native one, they are called from MetaModel.recompute


def records_to_compute(self, field):
    """Return the records to compute for ``field``."""
    ids = self.all.tocompute.get(field, ())

    # Note: in theory that will recompute fields for record that do not need but it should not be much
    #  and it will avoid doing query to the DB to verify that those are calculated fields for group.
    to_return = self[field.model_name].browse(ids)
    if "res.partner" not in self:
        return to_return
    if FIELD_CANARY_NAME not in self["res.partner"]._fields:
        return to_return
    field_canary = self["res.partner"]._fields[FIELD_CANARY_NAME]
    # check if the field is a field of `res.partner`
    if field.model_name == "res.partner":
        #   check if force_recompute_canary is in the list of fields to recompute
        #   by calling `native_fields_to_compute`
        if field_canary in native_fields_to_compute(self):
            # check that the number of record to recompute is less than MIN_RECORDS_FOR_ASYNC_RECOMPUTE
            if (
                _count_record_ids_to_recompute(self, field)
                < MIN_RECORDS_FOR_ASYNC_RECOMPUTE
            ):
                # Add to the list of record to recompute for this field
                # the one of `force_recompute_canary`
                field_canary_to_compute_ids = self.all.tocompute.get(field_canary, ())
                to_return |= self[field.model_name].browse(field_canary_to_compute_ids)

    return to_return


api.Environment.records_to_compute = records_to_compute


def _count_record_ids_to_recompute(self, field):
    ids = self.all.tocompute.get(field, ())
    return len(ids)


def fields_to_compute(self):
    """Return a view on the field to compute."""
    fields = native_fields_to_compute(self)

    if "res.partner" not in self:
        return fields
    if FIELD_CANARY_NAME not in self["res.partner"]._fields:
        return fields
    field_canary = self["res.partner"]._fields[FIELD_CANARY_NAME]
    # First we check if the force_recompute_canary field is in the list
    if field_canary in fields:
        # If the field is the list, we check how many records need to be recomputed
        # record_count = _count_record_ids_to_recompute(self)
        if (
            _count_record_ids_to_recompute(self, field_canary)
            < MIN_RECORDS_FOR_ASYNC_RECOMPUTE
        ):
            # If the field is in the list and there is less than MIN_RECORDS_FOR_ASYNC_RECOMPUTE records
            # We replace the field force_recompute_canary by the list of fields to recompute
            # self.env["res.partner"]._get_calculated_group_fields()
            partner_fields_to_compute = self[
                "res.partner"
            ]._get_calculated_group_fields()
            to_return = self.all.tocompute.copy()
            partner_ids_to_compute = to_return[field_canary]
            del to_return[field_canary]
            for field in partner_fields_to_compute:
                if field.name == FIELD_CANARY_NAME:
                    continue
                to_return[field] = partner_ids_to_compute
            return to_return.keys()

    return fields


api.Environment.fields_to_compute = fields_to_compute
