import itertools

from odoo import fields
from odoo.tools import human_size


class DocumentBinaryField(fields.Binary):
    """Gets binary data from linked documents store based on given tag.
    Behaves similar to :class:`odoo.fields.Binary`.

    Donot use this field for computed or related fields.
    Use :class:`odoo.fields.Binary` instead.

    :param str documents_field: the One2many field containing linked documents.
    :param str get_tags_func: Func in the model to call to get Document tag(s).
    :param str get_storage_backend_func: Func in the model to call to get storage backend.
    """

    type = "binary"
    column_type = None
    prefetch = False
    _depends_context = ("bin_size",)

    documents_field: str = None
    get_tags_func: str = None
    get_storage_backend_func: str = None

    _tags = None
    _storage_backend = None

    def _get_attrs(self, model_class, name):
        attrs = super()._get_attrs(model_class, name)
        # DocumentField is treated as stored and not computed similar to
        # Attachment Binary field.
        attrs["store"] = True
        attrs["compute"] = False
        attrs["attachment"] = False

        docs_field = attrs.get("documents_field", None)
        attrs["_depends"] = list(attrs.get("_depends", []))
        if docs_field:
            attrs["_depends"].append(docs_field)
        attrs["_depends"] = tuple(attrs["_depends"])
        return attrs

    def setup_nonrelated(self, model):
        res = super().setup_nonrelated(model)
        assert self.documents_field in model._fields, "Field {} with unknown documents field {}".format(
            self,
            self.documents_field,
        )
        return res

    def read(self, records):
        # pylint: disable=method-required-super
        tags = self._get_tags_list(records)
        bin_size_name = "bin_size_" + self.name
        is_bin_size = records._context.get("bin_size") or records._context.get(bin_size_name)

        docs_list = []
        for rec in records:
            if not self.documents_field:
                # Some test cases causing error if none
                docs_list.append(None)
                continue
            domain = [("tags_ids", "=", tag.id) for tag in tags]
            doc = getattr(rec, self.documents_field).filtered_domain(domain)
            if not doc:
                docs_list.append(None)
            else:
                if is_bin_size:
                    docs_list.append(human_size(doc[0].file_size))
                else:
                    docs_list.append(doc[0].with_context(**{"bin_size": False, bin_size_name: False}).data)
        records.env.cache.insert_missing(records, self, docs_list)

    def create(self, record_values):
        # pylint: disable=method-required-super
        if not record_values:
            return
        env = record_values[0][0].env
        tags = self._get_tags_list(record_values[0][0])
        storage_backend = self._get_storage_backend(record_values[0][0])
        if not storage_backend:
            # Some test cases causing error if none
            return
        for rec, value in record_values:
            if value:
                doc = env["storage.file"].create(
                    {
                        "tags_ids": [(4, tag.id) for tag in tags],
                        "data": value,
                        "backend_id": storage_backend.id,
                    }
                )
                rec.write({self.documents_field: [(4, doc.id)]})

    def write(self, records, value):
        # pylint: disable=method-required-super
        env = records.env
        # discard recomputation of self on records
        env.remove_to_compute(self, records)

        # update the cache, and discard the records that are not modified
        cache = env.cache
        cache_value = self.convert_to_cache(value, records)
        records = cache.get_records_different_from(records, self, cache_value)
        if not records:
            return

        cache.update(records, self, itertools.repeat(cache_value))

        tags = self._get_tags_list(records)
        storage_backend = self._get_storage_backend(records)
        if not (tags and storage_backend):
            # Some test cases causing error if none
            return

        # retrieve the attachments that store the values, and adapt them
        for rec in records:
            domain = [("tags_ids", "=", tag.id) for tag in tags]
            doc = getattr(rec, self.documents_field).filtered_domain(domain)

            if doc:
                # First delete existing record
                doc.unlink()
            if value:
                # If data is present, create new one
                # Else anyway record was deleted.
                doc = env["storage.file"].create(
                    {
                        "tags_ids": [(4, tag.id) for tag in tags],
                        "data": value,
                        "backend_id": storage_backend.id,
                    }
                )
                rec.write({self.documents_field: [(4, doc.id)]})

    def _get_storage_backend(self, records):
        if not self._storage_backend:
            if not self.get_storage_backend_func:
                return None
            func = getattr(records, self.get_storage_backend_func)
            if not func:
                return None
            self._storage_backend = func()
        return self._storage_backend

    def _get_tags_list(self, records):
        if not self._tags:
            if not self.get_tags_func:
                return []
            func = getattr(records, self.get_tags_func)
            if not func:
                return []
            self._tags = func()
            if self._tags and not isinstance(self._tags, list):
                self._tags = [self._tags]
        return self._tags
