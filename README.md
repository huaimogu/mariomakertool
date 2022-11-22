# mariomakertool  
我自己在直播马里奥制造2时开发使用的一个小工具  
功能如下：  
(1)获取多人对战时当前人物角色，例如本局是小蓝还是马里奥，配合obs显示在直播间中  
(2)读取当前正在游玩的关卡信息，配合obs显示在直播间中  
(3)匹配识别玩家发送的对话内容，并播放出来  
使用方法：   
(1) 安装python环境，本人自己选的是3.10  
(2) 在项目中使用python -i requests.txt安装所需库  
(3) 使用python main.py运行软件  
注意点：   
(1) 需要安装obs虚拟摄像头插件：OBS-VirtualCam  
OBS 27 及以下: https://obsproject.com/forum/resources/obs-virtualcam.949/  
OBS 28 及以上: https://github.com/Avasam/obs-virtual-cam/releases  
在obs中选择采集卡设备 - 滤镜 - 虚拟摄像头 - 开启，然后在软件中选择虚拟摄像头和分辨率，开始监听。