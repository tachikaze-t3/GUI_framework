*** Settings ***
Library           NcsDriver
Library           ServerDriver
Suite Setup       Login To Ncs
Suite Teardown    Logout To Ncs

*** Comments ***
本ファイルはintall手順を実施するためのrobotファイル

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
    @{packages}[ncs560][active_1][exec]     :install active直後のshow install activeで表示されるパッケージ名
    @{packages}[ncs560][active_1][admin]    :install active直後のadmin show install activeで表示されるパッケージ名
    @{packages}[ncs560][active_2][exec]     :install deactive後のshow install activeで表示されるパッケージ名
    @{packages}[ncs560][active_2][admin]    :install deactive後のadmin show install activeで表示されるパッケージ名

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

*** Variables ***

*** Tasks ***
UT2-01
    [Documentation]    install activateの実施
    [Tags]    手順変更    動作未確認
    Install Activate    # 動作未確認
    Logout To Ncs
    Sleep    300s
    Wait Until Keyword Succeeds    55    60s    Login To Ncs    # 動作未確認
    ${exec_packages}    Show Install Active
    ${admin_packages}    Admin Show Install Active
    List Containts Should Be Equal    ${exec_packages}[0][Packages]    ${packages}[ncs560][active_1][exec]
    List Containts Should Be Equal    ${exec_packages}[1][Packages]    ${packages}[ncs560][active_1][admin]
    List Containts Should Be Equal    ${admin_packages}[0][Packages]    ${packages}[ncs560][active_1][exec]
    List Containts Should Be Equal    ${admin_packages}[1][Packages]    ${packages}[ncs560][active_1][admin]

UT2-02
    [Documentation]    各モジュールの正常性確認、RP0とRP1の同期確認
    [Tags]    動作未確認
    ${show_platform}               Show Platform
    Wait Until Keyword Succeeds    30             60s    Platform Should Be Equal    ${show_platform}            ${ncs}[platform]
    ${keyword_NSR_ready}           Create List    Standby node in 0/RP0/CPU0 is NSR-ready    Standby node in 0/RP1/CPU0 is NSR-ready
    @{command}                     Create List    show redundancy
    ${show_redundancy}             Get Log        ${command}
    ${keyword_ready}               Create List    Standby node in 0/RP0/CPU0 is ready        Standby node in 0/RP1/CPU0 is ready
    Wait Until Keyword Succeeds    5              60s    Should Contain Any          ${show_redundancy}          @{keyword_ready}
    Should Contain Any             ${show_redundancy}          @{keyword_NSR_ready}

UT2-03
    [Documentation]    OS version 確認
    ${version}    Show Version
    Should Be Equal    ${version}    7.3.2

UT2-04
    [Documentation]    install commitの実施
    [Tags]    動作未確認
    Install Commit    # 動作未確認

UT2-05
    [Documentation]    XR VM、Sysadmin VMのcommit packageの確認
    ${exec_packages}    Show Install Committed
    ${admin_packages}    Admin Show Install Committed
    List Containts Should Be Equal    ${exec_packages}[0][Packages]    ${packages}[ncs560][active_1][exec]
    List Containts Should Be Equal    ${exec_packages}[1][Packages]    ${packages}[ncs560][active_1][admin]
    List Containts Should Be Equal    ${admin_packages}[0][Packages]    ${packages}[ncs560][active_1][exec]
    List Containts Should Be Equal    ${admin_packages}[1][Packages]    ${packages}[ncs560][active_1][admin]

UT2-06
    [Documentation]    非アクティブ化
    [Tags]    動作未確認
    @{packages}    Create List    ncs560-isis-2.0.0.0-r732    ncs560-li-1.0.0.0-r732    ncs560-eigrp-1.0.0.0-r732
    Install Deactivate    ${packages}    # 動作未確認

UT2-07
    [Documentation]    install commitの実施
    [Tags]    動作未確認
    Install Commit    # 動作未確認
    
UT2-08
    [Documentation]    XR VM、Sysadmin VMのactive packageの確認
    ${exec_packages}    Show Install Active
    ${admin_packages}    Admin Show Install Active
    List Containts Should Be Equal    ${exec_packages}[0][Packages]    ${packages}[ncs560][active_2][exec]
    List Containts Should Be Equal    ${exec_packages}[1][Packages]    ${packages}[ncs560][active_2][admin]
    List Containts Should Be Equal    ${admin_packages}[0][Packages]    ${packages}[ncs560][active_2][exec]
    List Containts Should Be Equal    ${admin_packages}[1][Packages]    ${packages}[ncs560][active_2][admin]

UT2-09
    [Documentation]    XR VM、Sysadmin VMのcommit packageの確認
    ${exec_packages}    Show Install Committed
    ${admin_packages}    Admin Show Install Committed
    List Containts Should Be Equal    ${exec_packages}[0][Packages]    ${packages}[ncs560][active_2][exec]
    List Containts Should Be Equal    ${exec_packages}[1][Packages]    ${packages}[ncs560][active_2][admin]
    List Containts Should Be Equal    ${admin_packages}[0][Packages]    ${packages}[ncs560][active_2][exec]
    List Containts Should Be Equal    ${admin_packages}[1][Packages]    ${packages}[ncs560][active_2][admin]

UT2-10    
    [Documentation]    FPDのステータス確認
    ${output}            Show Hw Module Fpd
    Fpd Should Be UT2    ${output}

UT2-11
    [Documentation]    hw-module profile 設定(IOSXR-9535有効化)
    [Tags]    動作未確認
    @{config}    Create List    hw-module profile mpls-ext-dscp-preserve v4uc-enable
    Config Set    ${config}
    @{command}    Create List   show running-config | include hw-module profile
    ${output}    Get Log     ${command}
    Should Contain    ${output}    hw-module profile mpls-ext-dscp-preserve v4uc-enable

UT2-12
    [Documentation]    筐体再起動
    Ncs Reload
    Logout To Ncs

UT2-13
    [Documentation]    各モジュールの正常性確認、RP0とRP1の同期確認
    [Tags]    動作未確認
    Login To Ncs
    ${show_platform}               Show Platform
    Wait Until Keyword Succeeds    30             60s    Platform Should Be Equal    ${show_platform}            ${ncs}[platform]
    ${keyword_NSR_ready}           Create List    Standby node in 0/RP0/CPU0 is NSR-ready    Standby node in 0/RP1/CPU0 is NSR-ready
    @{command}                     Create List    show redundancy
    ${show_redundancy}             Get Log        ${command}
    ${keyword_ready}               Create List    Standby node in 0/RP0/CPU0 is ready        Standby node in 0/RP1/CPU0 is ready
    Wait Until Keyword Succeeds    5              60s    Should Contain Any          ${show_redundancy}          @{keyword_ready}
    Should Contain Any             ${show_redundancy}          @{keyword_NSR_ready}
