import time
from robot.api import logger
from robot.api.deco import library, keyword, not_keyword
from netmiko import ConnectHandler
from sshtunnel import SSHTunnelForwarder

@library(scope='SUITE')
class NcsDriver():
    """
    NcsDriverは、OROTI/SSMを踏み台としてNCS560/5504へSSH接続経由で操作を行うRobot Frameworkライブラリです。
    このライブラリはnetmikoを利用しています。
    """
    
    @keyword
    def create_tunnel(self, step_ip:str, step_username:str, step_password:str, ncs_ip:str, localhost_port):
        """
        create_tunnelは、OROTIを経由してNCSへ接続を行うためのSSHポートフォーワードを行います

        Args:
            step_ip (str): OROTI/SSMのIPアドレス
            step_username (str): OROTI/SSMへSSH接続する際のusername
            step_password (str): OROTI/SSMへSSH接続する際のpassword
            ncs_ip (str): NCSのIPアドレス
            localhost_port (str): SSHポートフォワードをする際のポート番号
        """
        self.server = SSHTunnelForwarder(
            (step_ip, 22),
            ssh_username= step_username,
            ssh_password= step_password,
            remote_bind_address= (ncs_ip, 22),
            local_bind_address= ('0.0.0.0', localhost_port)
        )
        self.localhost_port = localhost_port
        self.server.start()
    
    @keyword
    def delete_tunnel(self):
        """
        delete_tunnelは、OROTIM経由のSSHポートフォワードを終了します
        """
        self.server.close()
    
    @keyword
    def connect_to_ncs(self, ncs_username:str, ncs_password:str):
        """
        connect_to_ncsは、NCS560/5504へSSH接続を行います
        このメソッドはcreate_tunnelを使用後に使います

        Args:
            ncs_username (str): NCSへSSH接続する際のusername
            ncs_password (str): NCSへSSH接続する際のpassword
        """
        device = {
            'device_type': 'cisco_xr',
            'ip': 'localhost',
            'username': ncs_username,
            'password': ncs_password,
            'port': self.localhost_port,
            'session_log': 'ncs_session.log'
        }
        self.connection = ConnectHandler(**device)

    @keyword
    def disconnect_to_ncs(self):
        """
        disconnect_to_ncsは、NCS560/5504へのSSH接続を終了します
        """
        self.connection.disconnect()

    @keyword
    def get_log(self, command_list:list, wait_time=300) -> str:
        """
        get_logは、与えられたコマンドのログを取得します

        Args:
            command_list (list): 取得ログのコマンド
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで300秒
            
        Returns:
            output: 取得ログ
        """
        output = ''
        for command in command_list:
            output = f'\n{output}\n#{command}\n'
            output = output + self.connection.send_command(command, read_timeout=wait_time)
        logger.write(output, level='INFO')
        return output

    @keyword
    def admin_dir(self, address: str, location:str) ->list:
        """
        admin_dirは、引数に与えられたモジュールの情報を取得します
        ※location all以外、未対応

        Args:
            address (str, optional): 確認先のアドレス
            location (str, optional): 確認する媒体

        Returns:
            list: node,total,files,amountをkeyとするdictが格納されたlist
        """
        lines = self.connection.send_command(f'admin dir {address} location {location}')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        output = []
        module = {}
        files = []
        for line in lines:
            if len(line) >= 5:
                if line[:4] == 'node':
                    module['node'] = line.split()[1]
                    continue
                if line[:5] == 'total':
                    module['total'] = line.split()[1]
                    continue
            split = line.split()
            if module.get('total') != None:
                if split[1] == 'kbytes' and split[2] =='total':
                    store = []
                    for file in files:
                        store.append(file.split()[-1])
                    module['files'] = store
                    module['amount'] = line
                    output.append(module)
                    files = []
                    module = {}
                else:
                    files.append(line)
        return output

    @keyword
    def free_space_check(self, output_admin_dir: list, free_space: int) -> list:
        """
        free_space_checkは、admin_dirの出力から既定の容量より空き容量が少ないモジュールを出力します

        Args:
            output_admin_dir (list): admin_dirの出力結果
            free_space (int): 必要な空きスペース

        Returns:
            list: 空きスペースが指定の容量を下回ったモジュール名
        """
        output = []
        for dict in output_admin_dir:
            split = dict['amount'].split()
            if int(split[3][1:]) < free_space:
                output.append(dict['node'])
        return output

    @keyword
    def show_media(self, free_space=2.0) -> list:
        """
        show_mediaは、show media location allを取得し、引数で指定した容量以下のモジュール名を出力します

        Args:
            free_space (float): harddiskの空き容量(G)、デフォルト2.0

        Returns:
            list: 引数で指定した容量以下の空きharddiskのモジュール名
        """
        lines = self.connection.send_command('show media location all')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        node = ''
        output = []
        for line in lines:
            if len(line) > 5:
                if line[:5] == 'Media':
                    node = line.split('node')[1][:-1]
                    continue
                if line[:9] == 'harddisk:':
                    avail = line.split()[4]
                    if avail[-1] != 'G' or float(avail[:-1]) < free_space:
                        output.append(node)
                        continue
        return output
    
    @keyword
    def admin_show_media(self, free_space=2.0) -> list:
        """
        admin_show_mediaは、admin show media location allを取得し、引数で指定した容量以下のモジュール名を出力します

        Args:
            free_space (float): harddiskの空き容量(G)、デフォルト2.0

        Returns:
            list: 引数で指定した容量以下の空きharddiskのモジュール名
        """
        lines = self.connection.send_command('admin show media location all')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        node = ''
        output = []
        for line in lines:
            if len(line) > 10:
                if line[:10] == 'Location :':
                    node = line.split()[2]
                    continue
                if line[:9] == 'harddisk:':
                    avail = line.split()[4]
                    if avail[-1] != 'G' or float(avail[:-1]) < free_space:
                        output.append(node)
                        continue
        return output

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
    def chenge_run_mode(self, rsp_ip: str, wait_time=1):
        """
        change_run_modeは、runモードでのログインを行います

        Args:
            rsp_ip (str): RSPの内部IP
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command('admin', wait_time)
        output = output + self.channel_command('run', wait_time)
        output = output + self.channel_command(f'chvrf 0 ssh {rsp_ip}', wait_time)
        logger.write(output, level='INFO')

    @keyword
    def exit_run_mode(self, wait_time=1):
        """
        exit_run_modeは、runモードを終了します

        Args:
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command('exit', wait_time)
        output = output + self.channel_command('exit', wait_time)
        output = output + self.channel_command('exit', wait_time)
        logger.write(output, level='INFO')

    @keyword
    def current_destination(self, address: str, wait_time=1):
        """
        current_destinationは、引数で指定したアドレスにカレントディレクトリを移動します

        Args:
            address (str): 移動先のアドレス
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command(f'cd {address}', wait_time)
        logger.write(output, level='INFO')
        
    @keyword
    def file_check_ls(self, option = None, wait_time=1) -> str:
        """
        file_check_lsは、カレントディレクトリのファイルを表示します

        Args:
            option (_type_, optional): lsコマンドのオプション、デフォルトで入力なし
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒

        Returns:
            str: カレントディレクトリのファイル名
        """
        return self.channel_command(f'ls {option}', wait_time)

    @keyword
    def file_remove(self, file: str, location: str, wait_time=1):
        """
        file_removeは、引数で指定したファイルを削除します

        Args:
            file (str): 削除するファイル名
            location (str): 削除対象のモジュール
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command(f'rm {file} location {location}', wait_time)
        logger.write(output, level='INFO')

    @keyword
    def install_remove_inactive(self, packages=[]):
        """
        install_remove_inactiveは、install remove inactiveコマンドを実行します

        Args:
            packages (list): install removr inactiveで削除するパッケージ名、デフォルトで入力なし
        """
        option = ''
        for package in packages:
            option = option + ' ' + package
        output = self.connection.send_command(f'install remove inactive {option} synchronous')
        logger.write(output, level='INFO')

    @keyword
    def chenge_admin_mode(self, wait_time=1):
        """
        change_admin_modeは、adminモードに切り替えを行います

        Args:
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command('admin', wait_time)
        logger.write(output, level='INFO')
    
    @keyword
    def exit_admin_mode(self, wait_time=1):
        """
        exit_admin_modeは、adminモードを終了します

        Args:
            wait_time (int, optional):  コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command('exit', wait_time)
        logger.write(output, level='INFO')

    @keyword
    def admin_delete(self, filename: str, location: str, wait_time=10):
        """
        admin_deleteは、admin locationに存在する引数で指定したファイルを削除します

        Args:
            filename (str): 削除するファイル名
            location (str): RP指定
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで10秒
        """
        output = self.channel_command(f'admin delete {filename} location {location}', wait_time)
        if '[y|n][y] ?' in output:
            lines = self.channel_command('y', wait_time)
            output = output + lines
        logger.write(output, level='INFO')
        
    @keyword
    def file_delete(self, filename: str, location: str, wait_time=10):
        """
        file_deleteは、admin locationに存在する引数で指定したファイルを削除します

        Args:
            filename (str): 削除するファイル名
            location (str): RP指定
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1秒
        """
        output = self.channel_command(f'delete {filename} location {location}', wait_time)
        if '[confirm]' in output:
            lines = self.channel_command('', wait_time)
            output = output + lines
        logger.write(output, level='INFO')

    @keyword
    def scp_download(self, local_filename: str, remote_filename: str, 
                     host: str, username: str, password: str, vrf='', wait_time=1800):
        """
        scp_downloadは、scp通信によりファイルをダウンロードします

        Args:
            local_filename (str): 保存先アドレス
            remote_filename (str): ダウンロード元アドレス
            host (str): scpサーバーのホスト名
            username (str): scpサーバーのユーザー名
            password (str): scpサーバーのパスワード
            vrf (str, optional): VRF名、デフォルトは入力なし
            wait_time (int, optional): コマンド入力から出力を待つ時間、デフォルトで1800秒
        """
        output = ''
        if vrf != '':
            ouptut = self.channel_command(
                f'scp {username}@{host}:{remote_filename} vrf {vrf} {local_filename}', 5)
        else:
            output = self.channel_command(
                f'scp {username}@{host}:{remote_filename} {local_filename}', 5)
        output = output + self.connection.send_command_timing(password, read_timeout=wait_time)
        logger.write(output, level='INFO')

    @keyword
    def file_check_dir(self, address: str) -> list:
        """
        file_check_dirは、dirコマンドで表示したファイル名を取得します

        Args:
            address (str): アドレス

        Returns:
            list: ファイル名
        """
        lines = self.connection.send_command(f'dir {address}')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        lines.pop()
        lines.pop()
        output = []
        flag = False
        for line in lines:
            if flag != True:
                line = line.split()
                if len(line) >= 3:
                    if line[0] == 'Directory' and line[1] == 'of':
                        flag = True
                continue
            output.append(line.split()[-1])
        return output

    @keyword
    def config_set(self, config: list):
        """
        config_setは、引数で指定した設定を行います

        Args:
            config (list): 投入するコンフィグ
        """
        output = self.connection.config_mode()
        time.sleep(5)
        for line in config:
            output = output + self.connection.send_config_set(line)
        output = output + self.connection.send_config_set('commit')
        output = output + self.connection.send_config_set('exit')
        logger.write(output, level='INFO')

    @keyword
    def install_add(self, location: str, packages: list, wait_time=3600) -> str:
        """
        install_addは、引数のパッケージを指定してinstall addコマンドを実行します

        Args:
            location (str): パッケージの保存場所
            packages (list): パッケージ名
            wait_time (int, optional): 処理の待ち時間を指定します。デフォルトは3600秒

        Raises:
            AssertionError: 実行終了時に、successfullyの表示がない場合に表示

        Returns:
            str: 実行id
        """
        packages_str = ' '.join(packages)
        lines = self.connection.send_command(f'install add source {location} {packages_str} synchronous', read_timeout=wait_time)
        logger.write(lines, level='INFO')
        line = lines.splitlines()[-2]
        if line.split()[-1] != 'successfully':
            raise AssertionError('install addコマンドに失敗しました。')
        return line.split()[-3]

    @keyword
    def show_install_inactive(self, wait_time=60) -> list:
        """
        show_install_inactiveは、show install inactiveの出力結果をパースし、パッケージ名を出力します

        Args:
            wait_time (int, optional): 処理の待ち時間を指定します。デフォルトは60秒

        Returns:
            list: パッケージ名
        """
        lines = self.connection.send_command('show install inactive', read_timeout=wait_time)
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        output = []
        flag = False
        for line in lines:
            if "found" in line:
                flag = True
            else:
                if flag is True:
                    output.append(line.lstrip(' '))
        return output
    
    @keyword
    def platform_should_be_equal(self, output: list, anser:dict):
        """
        platform_should_be_equalは、show platformの出力から想定通りのモジュールが想定通りの状態であることを確認します

        Args:
            output (list): show platformの出力結果
            anser (dict): モジュール名と状態の情報

        Raises:
            AssertionError: 想定されたHW構成と異なる場合に表示します
        """
        if len(anser) != len(output):
            raise AssertionError('HW構成が想定と違います。') 
        for module in output:
            if module['Node'] not in anser:
                raise AssertionError('HW構成が想定と違います。') 
            if module['State'] != anser[module['Node']]:
                raise AssertionError('HW構成が想定と違います。') 

    @keyword
    def admin_show_install_inactive(self, wait_time=60) -> list:
        """
        admin_show_install_inactiveは、admin show install inactiveの出力結果をパースして出力します

        Args:
            wait_time (int, optional): 処理の待ち時間を指定します。デフォルトは60秒

        Returns:
            list: 'Node'と'Pacages'の情報を持ったdict型を格納
        """
        lines = self.connection.send_command('admin show install inactive', read_timeout=wait_time)
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        output = []
        for line in lines:
            if "Node" in line:
                node = {
                    "Node": line.split()[1],
                    "Packages": []
                }
                output.append(node)
            elif "       " in line:
                output[-1]['Packages'].append(line.strip())
        return output

    @keyword
    def install_prepare_by_id(self, install_id: str, wait_time=3600):
        """
        install_prepare_by_idは、引数のidについてinstall prepareを実施するコマンドです

        Args:
            install_id (str): 実行id
            wait_time (int, optional): 処理の待ち時間を指定します。デフォルトは3600秒
        
        Raises:
            AssertionError: 実行終了時に、successfullyの表示がない場合に表示
        """
        lines = self.connection.send_command(f'install prepare id {install_id}  synchronous', read_timeout=wait_time)
        logger.write(lines, level='INFO')
        line = lines.splitlines()[-2]
        if line.split()[-1] != 'successfully':
            raise AssertionError('install prepareコマンドに失敗しました。')

    @keyword
    def install_prepare(self, packages: list, wait_time=3600):
        """
        install_prepareは、引数のパッケージについてinstall prepareを実施するコマンドです

        Args:
            packages (list): パッケージ名
            wait_time (int, optional): 処理の待ち時間を指定します。デフォルトは3600秒

        Raises:
            AssertionError:  実行終了時に、successfullyの表示がない場合に表示
        """
        packages_str = " ".join(packages)
        lines = self.connection.send_command(f'install prepare id {packages_str}  synchronous', read_timeout=wait_time)
        logger.write(lines, level='INFO')
        line = lines.splitlines()[-2]
        if line.split()[-1] != 'successfully':
            raise AssertionError('install prepareコマンドに失敗しました。')

    @keyword
    def show_install_prepare(self) -> list:
        """
        show_install_prepareは、show install prepareで表示されたパッケージ名を取得します

        Returns:
            list: パッケージ名
        """
        lines = self.connection.send_command('show install prepare')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        flag = False
        output = []
        for line in lines:
            if "Prepared Packages" in line:
                flag = True
            else:
                if flag is True:
                    if line == "":
                        break
                    output.append(line.lstrip(" "))
        return output

    @keyword
    def show_platform(self) -> list:
        """
        show_platform

        Returns:
            list: Node,Type,State,Config Stateを持ったdict型
        """
        lines = self.connection.send_command('show platform')
        logger.write(lines, level='INFO')
        lines = lines.splitlines()
        output = []
        counter = 0
        for line in lines:
            if counter <= 3:
                counter += 1
                continue
            state = {
                "Node":line[0:17].strip(),
                "Type":line[18:44].strip(),
                "State":line[45:62].strip(),
                "Config State":line[63:79].strip()
            }
            output.append(state)
        return  output

    @keyword
    def show_md5(self, location: str, filename: str) -> str:
        """
        show_md5は、show_md5コマンドにより指定したファイルのチェックサムを確認します

        Args:
            location (str): ファイルが存在するディレクトリ
            filename (str): ファイル名

        Returns:
            str: チェックサム
        """
        lines = self.connection.send_command(f'show md5 file /{location}:/{filename}')
        logger.write(lines, level='INFO')
        return lines.splitlines()[-1]

    @keyword
    def list_containts_should_be_equal(self, list_x: list, list_y: list):
        """
        list_containts_should_be_equalは、入力された2つのlistの要素が同一かどうかを確認します。(要素は順不同)

        Args:
            list_x (list): 比較するlist
            list_y (list): 比較するlist

        Raises:
            AttributeError: 2つのlistの要素が同一出ない場合に表示
        """
        if len(list_x) != len(list_y):
            raise AttributeError('2つのlistは同一ではありません。')
        for contain_x in list_x:
            flag = False
            for contain_y in list_y:
                if contain_x == contain_y:
                    flag = True
            if flag == False:
                raise AttributeError('2つのlistは同一ではありません。')
