import os

from json import load as json_load


def load_params_list(params_path: str) -> dict[str: bool]:
    with open(params_path, 'r') as params_file:
        return {
            param['param_name']: param['is_required']
            for param in json_load(params_file)
        }


def load_params(params_list: dict[str: bool]) -> dict[str: str]:
    params = dict()
    for param_name, is_required in params_list.items():
        param_value = os.getenv(param_name, None)
        if param_value is None:
            if is_required:
                raise ValueError('Missing ENV parameter')
        else:
            params[param_name] = param_value
    return params


def get_params(params_path: str) -> dict[str: str]:
    return load_params(
        load_params_list(params_path)
    )
