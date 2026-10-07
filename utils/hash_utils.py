import hashlib


def compute_md5(file_path):

    try:

        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as file:

            while True:

                chunk = file.read(4096)

                if not chunk:
                    break

                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    except Exception as error:

        print(f"Hash calculation error: {error}")

        return None