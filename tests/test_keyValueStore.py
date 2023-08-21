import pytest
from src.key_value_store import KeyValueStore

class TestKeyValueStore():
    def test_get(self):
        kvs = KeyValueStore(server_name="DorianGray")
        kvs.data = {"Sibyl": "cruelty"}
        assert kvs.get("Sibyl") == "cruelty"

    def test_set(self):
        kvs = KeyValueStore(server_name="DorianGray")
        kvs.set("Sibyl", "cruelty")
        assert kvs.get("Sibyl") == "cruelty"

    def test_delete(self):
        kvs = KeyValueStore(server_name="DorianGray")
        kvs.data = {"Sibyl": "cruelty"}
        kvs.delete("Sibyl")
        assert kvs.get("Sibyl") == "Key Does Not Exist!"

