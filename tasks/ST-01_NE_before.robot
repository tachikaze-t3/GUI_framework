*** Settings ***
Library    SshDriver
Suite Setup       Login To Ncs
Suite Teardown    Logout To Ncs

*** Comments ***
YAMLで設定が必要なパラメータ
    ${oroti}[ip]                            :orotiへssh接続する際のIPアドレス
    ${oroti}[cli_username]                  :orotiへssh接続する際のユーザー名
    ${oroti}[cli_password]                  :orotiへssh接続する際のパスワード
    ${localhost_port}                       :sshポートフォワードに使用する作業端末のポート番号
    ${ncs}[ip]                              :ncsにssh接続する際のIPアドレス
    ${ncs}[username]                        :ncsにssh接続する際のユーザー名
    ${ncs}[password]                        :ncsにssh接続する際のパスワード
    ${ncs}[installer_dir]                   :scpダウンロードを行う際の保存先ディレクトリ
    ${before_log}                           :事前ログで取得するコマンド
    ${scp_server}[host]                     :scpサーバーのhost名
    ${scp_server}[username]                 :scpダウンロードの際に必要なユーザー名
    ${scp_server}[password]                 :scpダウンロードの際に必要なパスワード
    ${scp_server}[vrf]                      :scpサーバーに接続するためのvrf(ncs側)
    ${scp_server}[dir]                      :scpサーバーのファイルが保存されているディレクトリアドレス
    @{packages}[ncs560][inactive][exec]     :show install inactiveで表示されるパッケージ名
    @{packages}[ncs560][inactive][admin]    :admin show install inactiveで表示されるパッケージ名

*** Variables ***


*** Keywords ***
Login To Ncs
    [Documentation]    SSHポートフォワードを行い、OROTI経由でNCSへSSH接続を行います
    Create Tunnel     ${oroti}[ip]        ${oroti}[cli_username]    ${oroti}[cli_password]    ${ncs}[ip]    ${localhost_port}
    Connect To Ncs    ${ncs}[username]    ${ncs}[password]

Logout To Ncs
    [Documentation]    NCSとのSSH接続を終了し、SSHポートフォワードを終了します
    Disconnect To Ncs
    Delete Tunnel

*** Tasks ***

UT1-00
    [Documentation]    事前ログ取得
    [Tags]    作りかけ
    Get Log                 ${before_log}
    ${show_platform}        Show Platform
    # show platの正解トリガー不明(NodeとStateを確認)
    Log                     ${show_platform}
    ${keyword_ready}        Create List           Standby node in 0/RP0/CPU0 is ready    Standby node in 0/RP1/CPU0 is ready
    ${keyword_NSR_ready}    Create List           Standby node in 0/RP0/CPU0 is NSR-ready    Standby node in 0/RP1/CPU0 is NSR-ready
    @{command}              Create List           show redundancy
    ${show_redundancy}      Get Log               ${command}
    Should Contain Any      ${show_redundancy}    @{keyword_ready}
    Should Contain Any      ${show_redundancy}    @{keyword_NSR_ready}

UT1-01
    [Documentation]    ディスク容量の確認
    Admin Dir          harddisk:    all
    Show Media
    Admin Show Media

UT1-02
    [Documentation]    coreファイルの削除
    Admin Dir          harddisk:*core*    all
    Admin Delete       harddisk:*core*    0/RP0
    Admin Delete       harddisk:*core*    0/RP1
    File Delete        harddisk:*core*    0/RP0/CPU0
    File Delete        harddisk:*core*    0/RP1/CPU0
    ${admin_dir}       Admin Dir          harddisk:*core*    all
    Should Be Empty    ${admin_dir}

UT1-03
    [Documentation]    showtechファイルの削除
    Admin Dir          harddisk:/showtech      all
    Admin Delete       harddisk:/showtech/*    0/RP0
    Admin Delete       harddisk:/showtech/*    0/RP1
    File Delete        harddisk:/showtech/*    0/RP0/CPU0
    File Delete        harddisk:/showtech/*    0/RP1/CPU0
    ${admin_dir}       Admin Dir               harddisk:/showtech    all
    Should Be Empty    ${admin_dir}

UT1-04
    [Documentation]    hbmiss.tar.gzファイルの削除
    Admin Dir          harddisk:/*hbmiss*    all
    Admin Delete       harddisk:/*hbmiss*    0/RP0
    Admin Delete       harddisk:/*hbmiss*    0/RP1
    File Delete        harddisk:/*hbmiss*    0/RP0/CPU0
    File Delete        harddisk:/*hbmiss*    0/RP1/CPU0
    ${admin_dir}       Admin Dir             harddisk:/*hbmiss*    all
    Should Be Empty    ${admin_dir}

UT1-05
    [Documentation]    kdumpファイルの削除
    Admin Dir          harddisk:/*kdump*    all
    Admin Delete       harddisk:/*kdump*    0/RP0
    Admin Delete       harddisk:/*kdump*    0/RP1
    File Delete        harddisk:/*kdump*    0/RP0/CPU0
    File Delete        harddisk:/*kdump*    0/RP1/CPU0
    ${admin_dir}       Admin Dir            harddisk:/*kdump*    all
    Should Be Empty    ${admin_dir}

UT1-06
    [Documentation]    XR VM、Sysadmin VMのinactive packageの確認
    [Tags]    動作未確認
    @{admin_packages}    Create List    ncs560-sysadmin-hostos-7.0.1-r701.admin    ncs560-sysadmin-hostos-7.0.1-r701.host
    ${exec_output}       Show Install Inactive
    ${admin_output}      Admin Show Install Inactive
    Should Be Empty      ${exec_output}
    FOR    ${package}    IN    @{admin_packages}
        Should Contain    ${admin_output}[0][Packages]    ${package}
        Should Contain    ${admin_output}[1][Packages]    ${package}
    END

UT1-07
    [Documentation]    7.0.1用miniファイルの確認
    Admin Dir    harddisk:/tftpboot    all

UT1-08
    [Documentation]    OS/SMU 配信 (SCP) 
    [Tags]    動作未確認
    ${filename}     Set Variable             ${scp_server}[dir]ncs560-7.0.2.CSCvz20685.tar
    Scp Download    ${ncs}[installer_dir]    ${filename}    ${scp_server}[host]    ${scp_server}[username]    ${scp_server}[password]    ${scp_server}[vrf]
    FOR    ${package}    IN    @{packages}[ncs560][filename]
        ${filename}     Set Variable             ${scp_server}[dir]${package}
        Scp Download    ${ncs}[installer_dir]    ${filename}    ${scp_server}[host]    ${scp_server}[username]    ${scp_server}[password]    ${scp_server}[vrf]
    END

UT1-09
    [Documentation]    OS/SUM 配信確認
    ${output}         File Check Dir    harddisk:
    Should Contain    ${output}         ncs560-7.0.2.CSCvz20685.tar
    FOR    ${package}    IN    @{packages}[ncs560][filename]
        Should Contain    ${output}    ${package}
    END

UT1-10
    [Documentation]    XR VM側のfpd auto-upgrade の有効化
    @{command}    Create List    fpd auto-upgrade enable
    Config Set    ${command}

UT1-11
    [Documentation]    fpd auto-upgrade の設定確認
    @{exec_command}     Create List        show running-config | include fpd
    @{admin_command}    Create List        admin show running-config | include fpd
    ${exec_output}      Get Log            ${exec_command}
    ${admin_output}     Get Log            ${admin_command}
    Should Contain      ${exec_output}     fpd auto-upgrade enable
    Should Contain      ${admin_output}    fpd auto-upgrade enable

UT1-12
    [Documentation]    切り戻し用のSMU（7.0.2）のインストール
    [Tags]    動作未確認
    Install Add    harddisk:    ncs560-7.0.2.CSCvz20685.tar

UT1-13
    [Documentation]    OS / SMUのインストール
    [Tags]    動作未確認    修正
    Install Add    harddisk:    ${packages}[ncs560][filename]

UT1-14
    [Documentation]    XR VM、Sysadmin VMのinactive packageの確認
    ${exec_output}     Show Install Inactive
    ${admin_output}    Admin Show Install Inactive
    FOR    ${package}    IN    @{packages}[ncs560][inactive][exec]
        Should Contain    ${exec_output}   ${package} 
    END
    FOR    ${package}    IN    @{packages}[ncs560][inactive][admin]
        Should Contain    ${admin_output}[0][Packages]    ${package}
        Should Contain    ${admin_output}[1][Packages]    ${package}
    END

UT1-15
    [Documentation]    アクティブ化前のチェック
    [Tags]    動作未確認    手順変更
    @{prepare_packages}    Create List    @{packages}[ncs560][inactive][exec]    @{packages}[ncs560][inactive][exec]	
    Install Prepare        ${prepare_packages}
    ${output}              Show Install Prepare
    FOR    ${package}    IN    @{prepare_packages}
        Should Contain    ${output}    ${package}
    END
