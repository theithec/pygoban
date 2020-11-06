import json
import requests


class NetPlayerMixin:
    conn = "http://localhost:5000/"

    def set_turn(self, result):
        super().set_turn(result)
        requests.post(self.conn, json.dump(result))
