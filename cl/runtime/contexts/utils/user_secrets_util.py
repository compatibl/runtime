# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from pathlib import Path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cl.runtime.settings.project_settings import ProjectSettings


class UserSecretsUtil:
    """Util for user secrets rsa private cert."""

    @staticmethod
    def get_rsa_private_key() -> RSAPrivateKey:
        filepath = Path(ProjectSettings.instance().project_root) / "deployment/.secrets/private_key.pem"

        if not os.path.exists(filepath):
            UserSecretsUtil.generate_rsa_private_key()

        with open(filepath, "rb") as key_file:
            data = key_file.read()
            return serialization.load_pem_private_key(data, password=None, backend=default_backend())

    @staticmethod
    def get_rsa_public_key(private_key: RSAPrivateKey) -> str:
        public_key_obj = private_key.public_key()
        public_key = public_key_obj.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return public_key.decode()

    @staticmethod
    def generate_rsa_private_key():
        # Generate private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

        # Convert private key to PEM format
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        filepath = Path(ProjectSettings.instance().project_root) / "deployment/.secrets/private_key.pem"

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as file:
            file.write(pem)