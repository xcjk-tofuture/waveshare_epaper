import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID
from esphome.core import CORE, coroutine_with_priority

CODEOWNERS = ["@OttoWinter"]
DEPENDENCIES = ["network"]


def AUTO_LOAD():
    if CORE.using_arduino:
        return ["async_tcp"]
    if CORE.using_esp_idf:
        return ["web_server_idf"]
    return []


web_server_base_ns = cg.esphome_ns.namespace("web_server_base")
WebServerBase = web_server_base_ns.class_("WebServerBase", cg.Component)

CONF_WEB_SERVER_BASE_ID = "web_server_base_id"
CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(WebServerBase),
    }
)


@coroutine_with_priority(65.0)
async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(cg.RawExpression(f"{web_server_base_ns}::global_web_server_base = {var}"))

    if CORE.using_arduino:
        if CORE.is_esp32:
            cg.add_library("WiFi", None)
            cg.add_library("FS", None)
            cg.add_library("Update", None)
        if CORE.is_esp8266:
            cg.add_library("ESP8266WiFi", None)
        # https://github.com/ESP32Async/ESPAsyncWebServer/blob/main/library.json
        cg.add_library("ESP32Async/ESPAsyncWebServer", "3.7.10")
