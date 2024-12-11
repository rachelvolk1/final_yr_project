def convert_hyperparams(hyperparams):
    def strtobool(value):
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return value

    def handle_numbers(value):
        if isinstance(value, bool):
            return value  # Bypass boolean values
        try:
            if isinstance(value, str):
                if '.' in value:
                    return float(value)
                return int(value)
        except (ValueError, TypeError):
            return value

    return {k: handle_numbers(strtobool(v)) for k, v in hyperparams.items()}
