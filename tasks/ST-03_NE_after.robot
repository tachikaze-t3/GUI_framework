*** Settings ***
Library           NcsDriver
Library           ServerDriver
Suite Setup       Login To Ncs
Suite Teardown    Logout To Ncs

*** Comments ***
本ファイルは事前作業を実施するためのrobotファイル

YAMLで設定が必要なパラメータ
    ${oroti}[vip]                           :orotiにssh接続する際のVIP
    ${oroti}[username]                      :orotiにssh接続する際のusername
    ${oroti}[password]                      :orotiにssh接続する際のpassword
    ${oroti}[node][hostname]                :orotiのhostname一覧
    ${oroti}[node][ip]                      :orotiの各ノードのIPアドレス
    ${localhost_port}                       :sshポートフォワードに使用する作業端末のポート番号
    ${ncs}[ip]                              :ncsにssh接続する際のIPアドレス
    ${ncs}[username]                        :ncsにssh接続する際のユーザー名
    ${ncs}[password]                        :ncsにssh接続する際のパスワード
    ${ncs}[hostname]                        :ncsのhostname
    ${ncs}[installer_dir]                   :scpダウンロードを行う際の保存先ディレクトリ
    ${ncs}[platform]                        :show platformで出力されるNodeとStateの組み合わせ
    @{packages}[ncs560][filename]           :7.3.2のOS/SUMファイル
    ${after_log}                            :事後ログで取得するコマンド

*** Variables ***


*** Keywords ***
Login To Ncs
    [Documentation]    SSHポートフォワードを行い、OROTI経由でNCSへSSH接続を行います
    Connect To Server        ${oroti}[vip]             ${oroti}[username]    ${oroti}[password]
    ${secondary_hostname}    Get Secondary Hostname    ${oroti}[node][hostname]
    Disconnect To Server
    Create Tunnel            ${oroti}[node][ip][${secondary_hostname}]       ${oroti}[username]
    ...                      ${oroti}[password]    ${ncs}[ip]    ${localhost_port}
    Connect To Ncs           ${ncs}[username]          ${ncs}[password]      ncs_session-1.log
    @{command}               Create List               show running-config | include hostname
    ${output}                Get Log                   ${command}
    Should Contain           ${output}                 ${ncs}[hostname]

Logout To Ncs
    [Documentation]    NCSとのSSH接続を終了し、SSHポートフォワードを終了します
    Disconnect To Ncs
    Delete Tunnel

*** Tasks ***
UT3-01
    [Documentation]    FPDのステータス確認
    [Tags]    動作未確認
    ${output}            Show Hw Module Fpd
    Fpd Should Be UT3    ${output}

UT3-02
    [Documentation]    fpd auto-reload enable、設定変更確認
    [Tags]    動作未確認
    @{config}    Create List    fpd auto-reload enable
    Config Set    ${config}
    @{command}    Create List   show running-config | include fpd
    ${output}    Get Log     ${command}
    Should Contain    ${output}    fpd auto-reload enable

UT3-03
    [Documentation]    OS/SMUファイルの削除
    [Tags]    動作未確認
    File Delete    harddisk:ncs560-7.0.2.CSCvz20685.tar    all
    FOR    ${filename}    IN    @{packages}[ncs560][filename]
        File Delete    ${filename}    all
    END

UT3-04
    [Documentation]    OS/SMU ファイルの削除確認
    ${output}    File Check Dir     harddisk: | include 7.3.2
    Should Be Empty    ${output}
    ${output}    File Check Dir     harddisk: | include 7.0.2
    Should Be Empty    ${output}

UT3-05
    [Documentation]    事後ログの取得
    Get Log    ${after_log}