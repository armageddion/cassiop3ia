echo "Writing Alfr3d speak services file"
echo "[Unit]
Description=Alfr3d Speak service
Documentation=https://https://github.com/armageddion/cassiop3ia
Wants=network-online.target
After=network-online.target kafka.service

[Service]
User=alfr3d
Group=alfr3d
Type=simple
Restart=on-failure
ExecStart=python3 /opt/alfr3d/alfr3d_speak/speak.py

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/alfr3d_speak.service

echo "Setting up Alfr3d speak services"
chmod 644 /etc/systemd/system/alfr3d_speak.service


echo "Writing Alfr3d environment services file"
echo "[Unit]
Description=Alfr3d Environment service
Documentation=https://https://github.com/armageddion/cassiop3ia
Wants=network-online.target
After=network-online.target kafka.service

[Service]
User=alfr3d
Group=alfr3d
Type=simple
Restart=on-failure
ExecStart=python3 /opt/alfr3d/alfr3d_environment/environment.py

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/alfr3d_environment.service

echo "Setting up Alfr3d environment services"
chmod 644 /etc/systemd/system/alfr3d_environment.service


echo "Writing Alfr3d devices services file"
echo "[Unit]
Description=Alfr3d Devices service
Documentation=https://https://github.com/armageddion/cassiop3ia
Wants=network-online.target
After=network-online.target kafka.service

[Service]
User=alfr3d
Group=alfr3d
Type=simple
Restart=on-failure
ExecStart=python3 /opt/alfr3d/alfr3d_device/deviceClass.py

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/alfr3d_device.service

echo "Setting up Alfr3d device services"
chmod 644 /etc/systemd/system/alfr3d_device.service


echo "Writing Alfr3d user services file"
echo "[Unit]
Description=Alfr3d User service
Documentation=https://https://github.com/armageddion/cassiop3ia
Wants=network-online.target
After=network-online.target kafka.service

[Service]
User=alfr3d
Group=alfr3d
Type=simple
Restart=on-failure
ExecStart=python3 /opt/alfr3d/alfr3d_user/userClass.py

[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/alfr3d_user.service

echo "Setting up Alfr3d user services"
chmod 644 /etc/systemd/system/alfr3d_user.service


echo "Enabling Alfr3d's services"
systemctl daemon-reload
systemctl enable alfr3d_speak
systemctl enable alfr3d_environment
systemctl enable alfr3d_device
systemctl enable alfr3d_user

echo "Starting Alfr3d's services"
systemctl start alfr3d_speak
systemctl start alfr3d_environment
systemctl start alfr3d_device
systemctl start alfr3d_user