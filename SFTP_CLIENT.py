import os
from typing import List

import paramiko
from paramiko import SFTPClient, SFTPAttributes

from config import Config


class ManualCancel(Exception):
    pass


class Sftp:
    def __init__(self,host=Config.host, username=Config.username, password=Config.password):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password)
        self.host = host
        self.username = username
        self.connection: SFTPClient = self.ssh.open_sftp()

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.close()
        self.ssh.close()
        print(f"Disconnected from host")

    def download(self, remote_path, target_local_path, callback=None):
        """
        Downloads the file from remote sftp server to local.
        Also, by default extracts the file to the specified target_local_path
        """

        try:
            print(
                f"downloading from {self.host} as {self.username} [(remote path : {remote_path});(local path: {target_local_path})]"
            )

            # Create the target directory if it does not exist
            path, _ = os.path.split(target_local_path)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception as err:
                    raise Exception(err)

            # Download from remote sftp server to local
            self.connection.get(remote_path, target_local_path, callback=callback)
            print("download completed")
        except ManualCancel as err:
            print("download canceled")
        except Exception as err:
            print("download failed")
            raise Exception(err)

    def list_files(self, path='.'):
        return self.connection.listdir(path)

    def list_files_attr(self, path='.') -> List[SFTPAttributes]:
        return self.connection.listdir_attr(path)

    def get_file_size(self, path):
        return self.connection.stat(path).st_size
