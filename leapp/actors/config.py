"""
Config file format:
    yaml file like this:

---
# Note: have to add a fields.Map type before we can use yaml mappings.
section_name:
    field1_name: value
    field2_name:
        - listitem1
        - listitem2
section2_name:
    field3_name: value

Config files are any yaml files in /etc/leapp/actor_config.d/
(This is settable in /etc/leapp/leapp.conf)

"""
__metaclass__ = type

import abc
import glob
import logging
import os.path
from collections import defaultdict

import six
import yaml

from leapp.models.fields import ModelViolationError


try:
    # Compiled versions if available, for speed
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader


_ACTOR_CONFIG = None

log = logging.getLogger('leapp.actors.config')


class SchemaError(Exception):
    """
    Raised when actors use conflicting schemas.

    For example, one schema wants `section.field` to be an integer and other schema wants
    `section.field` to be a string.
    """


class ValidationError(Exception):
    """
    Raised when a config file fails to validate against any of the available schemas.
    """


# pylint: disable=deprecated-decorator
# @abc.abstractproperty is deprecated in newer Python3 versions but it's
# necessary for Python <= 3.3 (including 2.7)
@six.add_metaclass(abc.ABCMeta)
class Config:
    """
    An Actor config schema looks like this.

    ::
        class RHUIConfig(Config):
            section = "rhui"
            name = "file_map"
            type_ = fields.Map(fields.String())
            description = 'Description here'
            default = {"repo": "url"}
    """
    @abc.abstractproperty
    def section(self):
        pass

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractproperty
    def type_(self):
        pass

    @abc.abstractproperty
    def description(self):
        pass

    @abc.abstractproperty
    def default(self):
        pass

    @classmethod
    def to_dict(cls):
        """
        Return a dictionary representation of the config item that would be suitable for putting
        into a config file.
        """
        representation = {
            cls.section: {
                '{0}_description__'.format(cls.name): cls.description
            }
        }
        # TODO: Retrieve the default values from the type field.
        # Something like this maybe:
        #   representation[cls.section][cls.name] = cls.type_.get_default()

        return representation

    @classmethod
    def serialize(cls):
        """
        :return: Serialized information for the config
        """
        return {
            'class_name': cls.__name__,
            'section': cls.section,
            'name': cls.name,
            'type': cls.type_.serialize(),
            'description': cls.description,
            'default': cls.default,
        }
# pylint: enable=deprecated-decorator


def _merge_config(configuration, new_config):
    """
    Merge two dictionaries representing configuration.  fields in new_config overwrite
    any existing fields of the same name in the same section in configuration.
    """
    for section_name, section in new_config.items():
        if section_name not in configuration:
            configuration[section_name] = section
        else:
            for field_name, field in section:
                configuration[section_name][field_name] = field


def _get_config(config_dir='/etc/leapp/actor_conf.d'):
    """
    Read all configuration files from the config_dir and return a dict with their values.
    """
    # We do not do a recursive walk to maintain Python2 compatibility, but we do
    # not expect rich config hierarchies, so no harm done.
    config_files = glob.glob(os.path.join(config_dir, '*'))
    config_files = [f for f in config_files if f.endswith('.yaml')]
    config_files.sort()

    configuration = {}
    for config_file in config_files:
        with open(config_file) as f:
            raw_cfg = f.read()

        try:
            parsed_config = yaml.load(raw_cfg, SafeLoader)
        except Exception as e:
            log.warning("Warning: unparsable yaml file %s in the config directory."
                        " Error: %s", config_file, str(e))
            raise

        _merge_config(configuration, parsed_config)

    return configuration


def normalize_schemas(schemas):
    """
    Merge all schemas into a single dictionary and validate them for errors we can detect.
    """
    added_fields = set()
    normalized_schema = defaultdict(dict)
    for schema in schemas:
        for field in schema:
            unique_name = (field.section, field.name)

            # Error if the field has been added by another schema
            if unique_name in added_fields and added_fields[unique_name] != field:
                # TODO: Also include information on what Actor contains the
                # conflicting fields but that information isn't passed into
                # this function right now.
                message = ('Two actors added incompatible configuration items'
                           ' with the same name for Section: {section},'
                           ' Field: {field}'.format(section=field.section,
                                                    field=field.name))
                log.error(message)
                raise SchemaError(message)

            # TODO: More validation here.

            # Store the fields from the schema in a way that we can easily look
            # up while validating
            added_fields.add(unique_name)
            normalized_schema[field.section][field.name] = field

    return normalized_schema


def _validate_field_type(field_type, field_value, field_path):
    """
    Return False if the field is not of the proper type.

    :param str field_path: Path in the config where the field is placed.
                           Example: A field 'target_clients' in a section 'rhui' would have a path 'rhui.target_clients'
    """
    try:
        # the name= parameter is displayed in error messages to let the user know what precisely is wrong
        field_type._validate_model_value(field_value, name=field_path)
    except ModelViolationError as e:
        # Any problems mean that the field did not validate.
        log.info("Configuration value failed to validate with: %s", e)
        return False
    return True


def _normalize_config(actor_config, schema):
    # Go through the config and log warnings about unexpected sections/fields.
    for section_name, section in actor_config.items():
        if section_name not in schema:
            # TODO: Also have information about which config file contains the unknown field.
            message = "A config file contained an unknown section: {section}".format(section=section_name)
            log.warning(message)
            continue

        for field_name in actor_config:
            # Any field names which end in "__" are reserved for LEAPP to use
            # for its purposes.  In particular, it places documentation of
            # a field's value into these reserved field names.
            if field_name.endswith("__"):
                continue

            if field_name not in schema[section_name]:
                # TODO: Also have information about which config file contains the unknown field.
                message = ("A config file contained an unknown field: (Section:"
                           " {section}, Field: {field})".format(
                               section=section_name, field=field_name)
                           )
                log.warning(message)

    # Do several things:
    # * Validate that the config values are of the proper types.
    # * Add default values where no config value was provided.
    normalized_actor_config = {}
    for section_name, section in schema.items():
        for field_name, field in section.items():
            # TODO: We might be able to do this using the default piece of
            # model.fields.Field().  Something using
            # schema[section_name, field_name].type_ with the value from
            # actor_config[section_name][field_name].  But looking at the Model
            # code, I wasn't quite sure how this should be done so I think this
            # will work for now.

            # For every item in the schema, either retrieve the value from the
            # config files or set it to the default.
            try:
                value = actor_config[section_name][field_name]
            except KeyError:
                # Either section_name or field_name doesn't exist
                section = actor_config[section_name] = actor_config.get(section_name, {})
                # May need to deepcopy default if these values are modified.
                # However, it's probably an error if they are modified and we
                # should possibly look into disallowing that.
                value = field.default
                section[field_name] = value

            field_path = '{0}.{1}'.format(section_name, field_name)
            if not _validate_field_type(field.type_, value, field_path):
                raise ValidationError("Config value for (Section: {section},"
                                      " Field: {field}) is not of the correct"
                                      " type".format(section=section_name,
                                                     field=field_name)
                                      )

            normalized_section = normalized_actor_config.get(section_name, {})
            normalized_section[field_name] = value
            # If the section already exists, this is a no-op.  Otherwise, it
            # sets it to the newly created dict.
            normalized_actor_config[section_name] = normalized_section

    return normalized_actor_config


def load(config_dir, schemas):
    """
    Return Actor Configuration.

    :returns: a dict representing the configuration.
    :raises ValueError: if the actor configuration does not match the schema.

    This function reads the config, validates it, and adds any default values.
    """
    global _ACTOR_CONFIG
    if _ACTOR_CONFIG:
        return _ACTOR_CONFIG

    config = _get_config(config_dir)
    config = _normalize_config(config, schemas)

    _ACTOR_CONFIG = config
    return _ACTOR_CONFIG


def retrieve_config(schema):
    """Called by the actor to retrieve the actor configuration specific to this actor."""
    # TODO: The use of _ACTOR_CONFIG isn't good API. Since this function is
    # called by the Actors, we *know* that this is okay to do (as the
    # configuration will have already been loaded.) However, there's nothing in
    # the API that ensures that this is the case.  Need to redesign this.
    # Can't think of how it should look right now because loading requires
    # information that the Actor doesn't know.

    configuration = defaultdict(dict)
    for field in schema:
        configuration[field.section][field.name] = _ACTOR_CONFIG[field.section][field.name]

    return dict(configuration)
