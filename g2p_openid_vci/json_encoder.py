import base64
import json
from datetime import date, datetime, timezone


class VCJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        if isinstance(obj, datetime):
            return (
                f'{obj.astimezone(tz=timezone.utc).replace(tzinfo=None).isoformat(timespec="milliseconds")}Z'
            )
        if isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

    @classmethod
    def python_dict_to_json_dict(cls, data: dict) -> dict:
        return json.loads(json.dumps(data, cls=cls))
