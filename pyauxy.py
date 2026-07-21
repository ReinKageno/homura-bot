def printc(message, color='default'):
    match color:
        case 'default':
            print(f'\033[0m{message}')
        case 'red':
            print(f'\033[31m{message}\033[0m')
        case 'green':
            print(f'\033[32m{message}\033[0m')
        case 'yellow':
            print(f'\033[33m{message}\033[0m')
        case 'blue':
            print(f'\033[34m{message}\033[0m')
        case 'magenta':
            print(f'\033[35m{message}\033[0m')
        case 'cyan':
            print(f'\033[36m{message}\033[0m')

def strc(message, color='default'):
    match color:
        case 'default':
            return f'\033[0m{message}'
        case 'red':
            return f'\033[31m{message}\033[0m'
        case 'green':
            return f'\033[32m{message}\033[0m'
        case 'yellow':
            return f'\033[33m{message}\033[0m'
        case 'blue':
            return f'\033[34m{message}\033[0m'
        case 'magenta':
            return f'\033[35m{message}\033[0m'
        case 'cyan':
            return f'\033[36m{message}\033[0m'