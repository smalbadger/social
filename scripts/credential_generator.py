import os

cred_file = """
username = '{username}'
password = '{password}'
"""

if __name__ == "__main__":

    resource_dir = os.path.join("..", "src", "resources")
    if not os.path.exists(resource_dir):
        # create resources directory
        os.mkdir(resource_dir)

    credential_dir = os.path.join(resource_dir, 'credentials')
    if not os.path.exists(credential_dir):
        # create credentials directory
        os.mkdir(credential_dir)

        # create __init__.py file
        with open(os.path.join(credential_dir, '__init__.py'), 'w') as f:
            f.write("")

    # query for linkedin credentials
    linkedin_username = input("Linkedin Username/Email: ")
    linkedin_pwd = input("Linkedin Password: ")

    # write linkedin credentials to ignored file
    with open(os.path.join(credential_dir, "linkedin.py"), 'w') as f:
        f.write(cred_file.format(username=linkedin_username, password=linkedin_pwd))
