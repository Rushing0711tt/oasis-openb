# Standard Library
import re

# external
from six import text_type

# internal
from stix2elevator.extension_definitions import (
    get_extension_definition_id
)
from stix2elevator.options import get_option_value, info, warn


def check_for_missing_policy(policy):
    return get_option_value("missing_policy") == policy


def convert_to_custom_name(name, separator="_"):
    if re.search('[A-Z]', name):
        warn("Custom name %s has been converted to all lower case", 727, name)
    # use custom_property_prefix for all custom names
    return "x" + separator + get_option_value("custom_property_prefix") + separator + name.lower()


def add_string_property_to_description(sdo_instance, property_name, property_value, is_list=False):
    if is_list:
        sdo_instance["description"] += "\n\n" + property_name.upper() + ":\n"
        property_values = []
        for v in property_value:
            property_values.append(text_type(v))
        sdo_instance["description"] += ",\n".join(property_values)
    else:
        sdo_instance["description"] += "\n\n" + property_name.upper() + ":\n\t" + text_type(property_value)
    warn("Appended %s to description of %s", 302, property_name, sdo_instance["id"])


def add_string_property_as_custom_property(sdo_instance, property_name, property_value, is_list=False):
    if is_list:
        property_values = list()
        for v in property_value:
            property_values.append(text_type(v))
        sdo_instance[convert_to_custom_name(property_name)] = ",".join(property_values)
    else:
        sdo_instance[convert_to_custom_name(property_name)] = text_type(property_value)
    warn("Used custom property for %s", 308, property_name + (" of " + sdo_instance["id"] if "id" in sdo_instance else ""))


def add_string_property_as_extension_property(container, property_name, property_value, sdo_id, is_list=False):
    if is_list:
        property_values = list()
        for v in property_value:
            property_values.append(text_type(v))
        container[property_name] = ",".join(property_values)
    else:
        container[property_name] = text_type(property_value)
    warn("Used extension property for %s", 313, property_name + (" of " + sdo_id if sdo_id else ""))


def handle_missing_string_property(container, property_name, property_value, sdo_id, is_list=False, is_sco=False):
    if property_value:
        if check_for_missing_policy("add-to-description"):
            if is_sco or "description" not in container:
                warn("Missing property %s is ignored, because there is no description property", 309,
                     ("'" + property_name + "'" + (" of " + sdo_id if sdo_id else "")))
            else:
                add_string_property_to_description(container, property_name, property_value, is_list)
        elif check_for_missing_policy("use-custom-properties"):
            add_string_property_as_custom_property(container, property_name, property_value, is_list)
        elif check_for_missing_policy("use-extensions"):
            add_string_property_as_extension_property(container, property_name, property_value, sdo_id, is_list)
        else:
            warn("Missing property %s is ignored", 307, ("'" + property_name + "'" + (" of " + sdo_id if sdo_id else "")))


def add_confidence_property_to_description(sdo_instance, confidence, parent_property_name):
    prefix = parent_property_name.upper() + " " if parent_property_name else ""
    if confidence is not None:
        sdo_instance["description"] += "\n\n" + prefix + "CONFIDENCE: "
        if confidence.value is not None:
            sdo_instance["description"] += text_type(confidence.value)
        if confidence.description is not None:
            sdo_instance["description"] += "\n\t" + prefix + "DESCRIPTION: " + text_type(confidence.description)
        warn("Appended Confidence type content to description %s", 304, ("of" + sdo_instance["id"] if "id" in sdo_instance else ""))


def add_confidence_property_as_custom_property(sdo_instance, confidence, parent_property_name=None):
    prefix = parent_property_name + "_" if parent_property_name else ""
    if confidence.value is not None:
        sdo_instance[convert_to_custom_name(prefix + "confidence")] = text_type(confidence.value)
    if confidence.description is not None:
        sdo_instance[convert_to_custom_name(prefix + "confidence_description")] = text_type(confidence.description)
    warn("Used custom properties for Confidence type content %s", 308, ("of" + sdo_instance["id"] if "id" in sdo_instance else ""))


def add_confidence_property_as_extension_property(container, confidence, id, parent_property_name=None):
    prefix = parent_property_name + "_" if parent_property_name else ""
    if confidence.value is not None:
        container[prefix + "confidence"] = text_type(confidence.value)
    if confidence.description is not None:
        container[prefix + "confidence_description"] = text_type(confidence.description)
    warn("Used extensions properties for Confidence type content of %s", 313, id)


def handle_missing_confidence_property(container, confidence, id, parent_property_name=None):
    if confidence and confidence.value:
        if check_for_missing_policy("add-to-description") and confidence:
            add_confidence_property_to_description(container, confidence, parent_property_name)
        elif check_for_missing_policy("use-custom-properties"):
            add_confidence_property_as_custom_property(container, confidence, parent_property_name)
        elif check_for_missing_policy("use-extensions"):
            add_confidence_property_as_extension_property(container, confidence, id, parent_property_name)
        else:
            warn("Missing property 'confidence' of %s is ignored", 307, id)


def add_statement_type_to_description(sdo_instance, statement, property_name):
    sdo_instance["description"] += "\n\n" + property_name.upper() + ":"
    has_value = False
    if statement.value:
        sdo_instance["description"] += text_type(statement.value)
        has_value = True
    if statement.descriptions:
        descriptions = []
        for d in statement.descriptions:
            descriptions.append(text_type(d.value))
        sdo_instance["description"] += (": " if has_value else "") + "\n\n\t".join(descriptions)
    if statement.source is not None:
        # FIXME: Handle source
        info("Source in %s is not handled, yet.", 815, sdo_instance["id"])
    if statement.confidence:
        add_confidence_property_to_description(sdo_instance, statement.confidence, property_name)
    warn("Appended Statement type content to description %s", 305, ("of" + sdo_instance["id"] if "id" in sdo_instance else ""))


def add_statement_type_as_custom_or_extension_property(statement):
    statement_json = {}
    if statement.value:
        statement_json["value"] = text_type(statement.value)
    if statement.descriptions:
        descriptions = []
        for d in statement.descriptions:
            descriptions.append(text_type(d.value))
        statement_json["description"] = " ".join(descriptions)
    if statement.source is not None:
        # FIXME: Handle source
        info("Source property in STIX 1.x statement is not handled, yet.", 815)
    if statement.confidence:
        handle_missing_confidence_property(statement_json, statement.confidence, None)
    return statement_json


def statement_type_as_custom_properties(sdo_instance, statement, property_name):
    if statement.value:
        sdo_instance[convert_to_custom_name(property_name)] = text_type(statement.value)
    if statement.descriptions:
        descriptions = []
        for d in statement.descriptions:
            descriptions.append(text_type(d.value))
        sdo_instance[convert_to_custom_name(property_name) + "_description"] = " ".join(descriptions)
    if statement.source is not None:
        # FIXME: Handle source
        info("Source property in STIX 1.x statement is not handled, yet.", 815)
    if statement.confidence:
        add_confidence_property_as_custom_property(sdo_instance, statement.confidence, property_name)


def statement_type_as_extension_properties(container, statement, property_name, id):
    if statement.value:
        container[property_name] = text_type(statement.value)
    if statement.descriptions:
        descriptions = []
        for d in statement.descriptions:
            descriptions.append(text_type(d.value))
        container[property_name + "_description"] = " ".join(descriptions)
    if statement.source is not None:
        # FIXME: Handle source
        info("Source property in STIX 1.x statement is not handled, yet.", 815)
    if statement.confidence:
        add_confidence_property_as_extension_property(container, statement.confidence, property_name, id)


def handle_missing_statement_properties(container, statement, property_name, id):
    if statement:
        if check_for_missing_policy("add-to-description"):
            add_statement_type_to_description(container, statement, property_name)
        elif check_for_missing_policy("use-custom-properties"):
            statement_type_as_custom_properties(container, statement, property_name)
            warn("Used custom properties for Statement type content of %s", 308, id)
        elif check_for_missing_policy("use-extensions"):
            statement_type_as_extension_properties(container, statement, property_name, id)
            warn("Used custom properties for Statement type content of %s", 308, id)
        else:
            warn("Missing property %s of %s is ignored", 307, property_name, id)


def collect_statement_type_as_custom_or_extension_property(statements):
    statements_json = []
    for s in statements:
        statements_json.append(add_statement_type_as_custom_or_extension_property(s))
    return statements_json


def handle_multiple_missing_statement_properties(container, statements, property_name, id):
    if statements:
        if len(statements) == 1:
            handle_missing_statement_properties(container, statements[0], property_name, id)
        else:
            if check_for_missing_policy("add-to-description"):
                for s in statements:
                    add_statement_type_to_description(container, s, property_name)
            elif check_for_missing_policy("use-custom-properties"):
                container[convert_to_custom_name(property_name + "s")] = \
                    collect_statement_type_as_custom_or_extension_property(statements)
            elif check_for_missing_policy("use-extensions"):
                container[property_name + "s"] = collect_statement_type_as_custom_or_extension_property(statements)
            else:
                warn("Missing property %s of %s is ignored", 307, property_name, id)


def handle_missing_tool_property(sdo_instance, tool):
    if tool.name:
        if check_for_missing_policy("add-to-description"):
            sdo_instance["description"] += "\n\nTOOL SOURCE:"
            sdo_instance["description"] += "\n\tname: " + text_type(tool.name)
        warn("Appended Tool type content to description of %s", 306, sdo_instance["id"])
    elif check_for_missing_policy("use-custom-properties"):
        sdo_instance[convert_to_custom_name("tool_source")] = text_type(tool.name)
    else:
        warn("Missing property 'name' %s is ignored", 307, ("of" + sdo_instance["id"] if "id" in sdo_instance else ""))


def determine_container_for_missing_properties(object_type, object_instance):
    if check_for_missing_policy("use-extensions"):
        extension_definition_id = get_extension_definition_id(object_type)
        if "extensions" in object_instance and extension_definition_id in object_instance["extensions"]:
            return object_instance["extensions"][extension_definition_id], extension_definition_id
        elif not extension_definition_id:
            warn("No extension-definition was found for STIX 1 type %s %s", 312, object_type, (("of " + object_instance["id"]) if "id" in object_instance else ""))
            return None, None
        else:
            container = dict()
            return container, extension_definition_id
    else:
        return object_instance, None


def fill_in_extension_properties(instance, container, extension_definition_id):
    if check_for_missing_policy("use-extensions") and container != dict():
        if extension_definition_id:
            if "extensions" not in instance:
                instance["extensions"] = dict()
            if extension_definition_id not in instance["extensions"]:
                instance["extensions"][extension_definition_id] = container


