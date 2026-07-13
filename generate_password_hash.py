from getpass import getpass
from services.auth import hash_password
password=getpass('New administrator password: ')
confirm=getpass('Confirm password: ')
if not password or password!=confirm: raise SystemExit('Passwords are empty or do not match.')
print('\nCopy this value into .streamlit/secrets.toml:\n')
print(hash_password(password))
