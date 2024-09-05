import json

from odoo import api, fields, models


class EncryptedPartner(models.Model):
    _inherit = "res.partner"

    encrypted_val = fields.Binary("Encrypted value", attachment=False)
    is_encrypted = fields.Boolean(default=False)

    @api.model
    def gather_fields_to_be_enc_from_dict(
        self,
        fields_dict: dict,
        prov,
        replace=True,
    ):
        to_be_enc = {}
        for each in prov.get_registry_fields_set_to_enc():
            if fields_dict and fields_dict.get(each, None):
                to_be_enc[each] = fields_dict[each]
                if replace:
                    fields_dict[each] = prov.registry_enc_field_placeholder
        return to_be_enc

    def create(self, vals_list):
        is_encrypt_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.encrypt_registry", default=False)
        )
        if not is_encrypt_fields:
            return super().create(vals_list)

        vals_list = [vals_list] if isinstance(vals_list, dict) else vals_list

        prov = self.env["g2p.encryption.provider"].get_registry_provider()
        for vals in vals_list:
            if vals.get("is_registrant", False):
                to_be_encrypted = self.gather_fields_to_be_enc_from_dict(vals, prov)
                vals["encrypted_val"] = prov.encrypt_data(json.dumps(to_be_encrypted).encode())
                vals["is_encrypted"] = True

        return super().create(vals_list)

    def write(self, vals):
        is_encrypt_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.encrypt_registry", default=False)
        )
        if not is_encrypt_fields:
            return super().write(vals)

        prov = self.env["g2p.encryption.provider"].get_registry_provider()
        encrypted_vals = self.get_encrypted_val()
        for rec, (is_encrypted, encrypted_val) in zip(self, encrypted_vals, strict=True):
            if rec.is_registrant or vals.get("is_registrant", False):
                if not is_encrypted:
                    rec_values_list = rec.read(prov.get_registry_fields_set_to_enc())[0]
                    rec_values_list.update(vals)
                    rec_values_list["is_encrypted"] = True
                    vals = rec_values_list
                else:
                    decrypted_vals = json.loads(prov.decrypt_data(encrypted_val or b"{}").decode())
                    decrypted_vals.update(vals)
                    vals = decrypted_vals
                to_be_encrypted = self.gather_fields_to_be_enc_from_dict(vals, prov)

                vals["encrypted_val"] = prov.encrypt_data(json.dumps(to_be_encrypted).encode())

        return super().write(vals)

    def _fetch_query(self, query, fields):
        res = super()._fetch_query(query, fields)
        fields = {field.name for field in fields}
        prov = self.env["g2p.encryption.provider"].get_registry_provider()
        enc_fields_set = prov.get_registry_fields_set_to_enc().intersection(fields)
        if not enc_fields_set:
            return res
        if len(fields) == 2 and "encrypted_val" in fields and "is_encrypted" in fields:
            return res

        is_decrypt_fields = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_encryption.decrypt_registry", default=False)
        )
        if not is_decrypt_fields:
            return res
        for record in self:
            is_encrypted, encrypted_val = record.get_encrypted_val()[0]
            if is_encrypted and encrypted_val:
                decrypted_vals = json.loads(prov.decrypt_data(encrypted_val).decode())

                for field_name in enc_fields_set:
                    if field_name in decrypted_vals and field_name in record and record[field_name]:
                        self.env.cache.set(record, self._fields[field_name], decrypted_vals[field_name])
        return res

    def get_encrypted_val(self):
        ret = self.with_context(bin_size=False).read(["is_encrypted", "encrypted_val"])
        return [(each.get("is_encrypted", False), each.get("encrypted_val", None)) for each in ret]
