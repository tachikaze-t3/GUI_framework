import time
from robot.api import logger
from robot.api.deco import library, keyword, not_keyword
from netmiko import ConnectHandler

@library(scope='SUITE')
class ServerDriver():
    """
    ServerDriverは、OROTI/SSMにSSHで接続を行い、操作をするRobot Frameworkライブラリです。
    このライブラリはnetmikoを利用しています。
    """
    
    @keyword
    def connect_to_server(self, server_ip: str, server_username: str, server_password: str):
        """
        connect_to_serverは、OROTI/SSMサーバーへSSH接続を行います

        Args:
            server_ip (str): 接続するサーバーのIPアドレス
            server_username (str): 接続するサーバーのusername
            server_password (str): 接続するサーバーのpassword
        """
        device = {
            'device_type': 'autodetect',
            'ip': server_ip,
            'username': server_username,
            'password': server_password,
            'port': 22,
            'session_log': f'{server_ip}_session.log'
        }
        self.connection = ConnectHandler(**device)
    
    @keyword
    def disconnect_to_server(self):
        """
        disconnect_to_serverは、サーバーへのSSH接続を終了します
        """
        self.connection.disconnect()
    
    @keyword
    def get_secondary_hostname(self, hostname_list: list) -> str:
        """
        get_secondary_hostnameは、OROTIのVIPへ接続しActiveのホストを確認、secondaryのホスト名を返します

        Args:
            hostname_list (list): ホスト名のリスト

        Returns:
            str: secondaryのホスト名
        """
        active_server = self.connection.send_command('hostname')
        i = 0
        for hostname in hostname_list:
            if hostname == active_server:
                hostname_list.pop(i)
                break
            i = i + 1
        return hostname_list[0]
    
    @not_keyword
    def channel_command(self, command: str, wait_time=1)-> str:
        """
        channel_commandは、特殊なモードでコマンド投入を行うためのメソッドです
        Robotファイルからの呼び出しは不可
        ※netmikoはrunモード未サポートのためwait_timeはよく確認すること

        Args:
            command (str): 投入するコマンド
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒

        Returns:
            str: コマンド投入後、wait_timeの間に出力されたログ
        """
        self.connection.write_channel(f'{command}\n')
        time.sleep(wait_time)
        return self.connection.read_channel()
    
    @keyword
    def scp_upload(self, local_filename: str, remote_filename: str, 
                   host: str, username: str, password: str, wait_time=1800 ):
        """
        scp_uploadは、サーバーからNCSにSCP通信でファイルをアップロードします

        Args:
            local_filename (str): アップロードするファイルアドレス
            remote_filename (str): アップロード先のアドレス
            host (str): アップロード先のホスト名
            username (str): アップロード先のusarname
            password (str): アップロード先のpassword
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1800秒
        """
        output = self.channel_command(
            f'scp {local_filename} {username}@{host}:{remote_filename}', 5)
        output = output + self.connection.send_command_timing(password, read_timeout=wait_time)
        logger.write(output, level='INFO')

    @keyword
    def file_check(self, address='') -> str:
        """
        file_checkは、指定したアドレスのファイルを取得します
        (ファイル名はカラーコードも含めて取得します)

        Args:
            address (str, optional): 確認するアドレス。デフォルトは入力なし

        Returns:
            str: lsコマンドの出力結果
        """
        output = self.connection.send_command_timing(f'ls -l {address}')
        logger.write(output, level='INFO')
        return output
