# -*- coding: utf-8 -*-

from leapp.utils.output import print_error


error = {'message': {'data': ('{"severity": "warning", "time": "2023-12-12T00:00:42", "actor": "An actor",'
                              '"message": "Нечакана"}')}}


def test_print_error_no_unicodedecodeerror():
    # Make sure no exception is raised
    print_error(error)
