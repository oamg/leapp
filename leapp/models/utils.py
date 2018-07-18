from leapp.models.fields import ModelMisuseError


def init_from_tuple(model_class, field_names, data):
    """
    Create an instance of the given model class and use the data to initialize the fields with it.

    :param model_class: Model class to initialize with the given data
    :param field_names: Names of the fields to be mapped from the tuple
    :param data: Data to initialize the Model from
    :type data: dict
    :return: Instance of this class
    """
    if len(field_names) != len(data):
        raise ModelMisuseError(
            'Number of field names do not match number of tuple elements while initializing ' + model_class.__name__)
    return model_class(**dict(zip(field_names, data)))
