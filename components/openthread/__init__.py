import esphome.codegen as cg
from esphome.components.esp32 import (
    VARIANT_ESP32C6,
    VARIANT_ESP32H2,
    add_idf_sdkconfig_option,
    only_on_variant,
)
from esphome.components.mdns import MDNSComponent
import esphome.config_validation as cv
from esphome.const import CONF_CHANNEL, CONF_ENABLE_IPV6, CONF_ID
import esphome.final_validate as fv

from .const import (
    CONF_DEVICE_TYPE,
    CONF_EXT_PAN_ID,
    CONF_FORCE_DATASET,
    CONF_MDNS_ID,
    CONF_MESH_LOCAL_PREFIX,
    CONF_NETWORK_KEY,
    CONF_NETWORK_NAME,
    CONF_PAN_ID,
    CONF_PSKC,
    CONF_SRP_ID,
    CONF_TLV,
)

CODEOWNERS = ["@mrene"]

AUTO_LOAD = ["network"]

# Wi-fi / Bluetooth / Thread coexistence isn't implemented at this time
# TODO: Doesn't conflict with wifi if you're using another ESP as an RCP (radio coprocessor), but this isn't implemented yet
CONFLICTS_WITH = ["wifi"]
DEPENDENCIES = ["esp32"]

CONF_DEVICE_TYPES = [
    "FTD",
    "MTD",
]


def set_sdkconfig_options(config):
    # and expose options for using SPI/UART RCPs
    add_idf_sdkconfig_option("CONFIG_IEEE802154_ENABLED", True)
    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_RADIO_NATIVE", True)

    # There is a conflict if the logger's uart also uses the default UART, which is seen as a watchdog failure on "ot_cli"
    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_CLI", False)

    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_ENABLED", True)

    if tlv := config.get(CONF_TLV):
        cg.add_define("USE_OPENTHREAD_TLVS", tlv)
    else:
        if pan_id := config.get(CONF_PAN_ID):
            add_idf_sdkconfig_option("CONFIG_OPENTHREAD_NETWORK_PANID", pan_id)

        if channel := config.get(CONF_CHANNEL):
            add_idf_sdkconfig_option("CONFIG_OPENTHREAD_NETWORK_CHANNEL", channel)

        if network_key := config.get(CONF_NETWORK_KEY):
            add_idf_sdkconfig_option(
                "CONFIG_OPENTHREAD_NETWORK_MASTERKEY", f"{network_key:X}".lower()
            )

        if network_name := config.get(CONF_NETWORK_NAME):
            add_idf_sdkconfig_option("CONFIG_OPENTHREAD_NETWORK_NAME", network_name)

        if (ext_pan_id := config.get(CONF_EXT_PAN_ID)) is not None:
            add_idf_sdkconfig_option(
                "CONFIG_OPENTHREAD_NETWORK_EXTPANID", f"{ext_pan_id:X}".lower()
            )
        if (mesh_local_prefix := config.get(CONF_MESH_LOCAL_PREFIX)) is not None:
            add_idf_sdkconfig_option(
                "CONFIG_OPENTHREAD_MESH_LOCAL_PREFIX", f"{mesh_local_prefix}".lower()
            )
        if (pskc := config.get(CONF_PSKC)) is not None:
            add_idf_sdkconfig_option(
                "CONFIG_OPENTHREAD_NETWORK_PSKC", f"{pskc:X}".lower()
            )

    if force_dataset := config.get(CONF_FORCE_DATASET):
        if force_dataset:
            cg.add_define("USE_OPENTHREAD_FORCE_DATASET")

    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_DNS64_CLIENT", True)
    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_SRP_CLIENT", True)
    add_idf_sdkconfig_option("CONFIG_OPENTHREAD_SRP_CLIENT_MAX_SERVICES", 5)

    # TODO: Add suport for sleepy end devices
    add_idf_sdkconfig_option(f"CONFIG_OPENTHREAD_{config.get(CONF_DEVICE_TYPE)}", True)


openthread_ns = cg.esphome_ns.namespace("openthread")
OpenThreadComponent = openthread_ns.class_("OpenThreadComponent", cg.Component)
OpenThreadSrpComponent = openthread_ns.class_("OpenThreadSrpComponent", cg.Component)

_CONNECTION_SCHEMA = cv.Schema(
    {
        cv.Optional(CONF_PAN_ID): cv.hex_int,
        cv.Optional(CONF_CHANNEL): cv.int_,
        cv.Optional(CONF_NETWORK_KEY): cv.hex_int,
        cv.Optional(CONF_EXT_PAN_ID): cv.hex_int,
        cv.Optional(CONF_NETWORK_NAME): cv.string_strict,
        cv.Optional(CONF_PSKC): cv.hex_int,
        cv.Optional(CONF_MESH_LOCAL_PREFIX): cv.ipv6network,
    }
)

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(OpenThreadComponent),
            cv.GenerateID(CONF_SRP_ID): cv.declare_id(OpenThreadSrpComponent),
            cv.GenerateID(CONF_MDNS_ID): cv.use_id(MDNSComponent),
            cv.Optional(CONF_DEVICE_TYPE, default="FTD"): cv.one_of(
                *CONF_DEVICE_TYPES, upper=True
            ),
            cv.Optional(CONF_FORCE_DATASET): cv.boolean,
            cv.Optional(CONF_TLV): cv.string_strict,
        }
    ).extend(_CONNECTION_SCHEMA),
    cv.has_exactly_one_key(CONF_NETWORK_KEY, CONF_TLV),
    cv.only_with_esp_idf,
    only_on_variant(supported=[VARIANT_ESP32C6, VARIANT_ESP32H2]),
)


def _final_validate(_):
    full_config = fv.full_config.get()
    network_config = full_config.get("network", {})
    if not network_config.get(CONF_ENABLE_IPV6, False):
        raise cv.Invalid(
            "OpenThread requires IPv6 to be enabled in the network component. "
            "Please set `enable_ipv6: true` in the `network` configuration."
        )


FINAL_VALIDATE_SCHEMA = _final_validate


async def to_code(config):
    cg.add_define("USE_OPENTHREAD")

    ot = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(ot, config)

    srp = cg.new_Pvariable(config[CONF_SRP_ID])
    mdns_component = await cg.get_variable(config[CONF_MDNS_ID])
    cg.add(srp.set_mdns(mdns_component))
    await cg.register_component(srp, config)

    set_sdkconfig_options(config)
