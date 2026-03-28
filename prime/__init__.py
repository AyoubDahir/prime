
__version__ = '0.0.1'


def _patch_frappe_sort_fields():
	"""
	Frappe bug: Document.__getattr__ returns '' for undefined attributes.
	When tabDocType has no field_order column, self.field_order is '' (not None/[]).
	The walrus operator in sort_fields assigns '' to field_order; since '' is falsy
	the if-block is skipped but field_order stays as str, causing:
	  AttributeError: 'str' object has no attribute 'append'
	Fix: use `or []` to convert any falsy value (including '') to a proper list.
	"""
	try:
		import frappe.model.meta as _meta
		import json as _json

		def _patched_sort_fields(self):
			if field_order := (getattr(self, "field_order", None) or []):
				field_order = [fn for fn in _json.loads(field_order) if fn in self._fields]
				if len(field_order) == len(self.fields):
					self._update_fields_based_on_order(field_order)
					return
				if self.fields[0].fieldname not in field_order:
					fields_to_prepend = []
					standard_field_found = False
					for fieldname, field in self._fields.items():
						if getattr(field, "is_custom_field", False):
							break
						if fieldname in field_order:
							standard_field_found = True
							break
						fields_to_prepend.append(fieldname)
					if standard_field_found:
						field_order = fields_to_prepend + field_order
					else:
						field_order = fields_to_prepend

			existing_fields = set(field_order) if field_order else False
			insert_after_map = {}

			for index, field in enumerate(self.fields):
				if existing_fields and field.fieldname in existing_fields:
					continue
				if not getattr(field, "is_custom_field", False):
					if existing_fields:
						insert_after_map.setdefault(self.fields[index - 1].fieldname, []).append(field.fieldname)
					else:
						field_order.append(field.fieldname)
				elif insert_after := getattr(field, "insert_after", None):
					insert_after_map.setdefault(insert_after, []).append(field.fieldname)
				else:
					field_order.insert(0, field.fieldname)

			if insert_after_map:
				_meta._update_field_order_based_on_insert_after(field_order, insert_after_map)

			self._update_fields_based_on_order(field_order)

		_meta.Meta.sort_fields = _patched_sort_fields
	except Exception:
		pass


_patch_frappe_sort_fields()
