echo "starting alfr3d danavation"
sudo systemctl restart alfr3d_danavation

echo "starting alfr3d device"
sudo systemctl restart alfr3d_device

echo "starting alfr3d environment"
sudo systemctl restart alfr3d_environment

echo "starting alfr3d google"
sudo systemctl restart alfr3d_google

echo "starting alfr3d lighting"
sudo systemctl restart alfr3d_lighting

echo "starting alfr3d speak"
sudo systemctl restart alfr3d_speak

echo "starting alfr3d user"
sudo systemctl restart alfr3d_user

echo "starting alfr3d daemon"
/opt/alfr3d/.venv/bin/python3  /opt/alfr3d/alfr3d_daemon/alfr3ddaemon.py restart

echo "starting log tail"
tail -f /var/log/alfr3d/alfr3d.log
