import os

cred_file = """
username = '{username}'
password = '{password}'
"""

if __name__ == "__main__":

    credential_dir = os.path.join("..", "src", "credentials")
    if not os.path.exists(credential_dir):
        # create credentials directory
        os.mkdir(credential_dir)

        # create __init__.py file
        with open(os.path.join(credential_dir, '__init__.py'), 'w') as f:
            f.write("")

    # query for linkedin credentials
    linkedin_pwd = input("Linkedin Password: ")
    linkedin_username = input("Linkedin Username/Email: ")

    # write linkedin credentials to ignored file
    with open(os.path.join(credential_dir, "linkedin.py"), 'w') as f:
        f.write(cred_file.format(username=linkedin_username, password=linkedin_pwd))
