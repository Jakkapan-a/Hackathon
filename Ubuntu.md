
```sh
curl -fsSL https://ollama.com/install.sh | sh
ollama pull scb10x/typhoon-ocr1.5-3b


watch -n 0.5 nvidia-smi

systemctl status ollama

ss -tulpn | grep 11434


sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo nano /etc/systemd/system/ollama.service.d/override.conf


[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"


sudo systemctl daemon-reload
sudo systemctl restart ollama


ถ้ายังไม่ได้สร้าง rule: ไปที่
VPC Network → Firewall rules → Create rule

Name: allow-ollama-11434

Direction: Ingress

Protocol: TCP

Port: 11434


```

INSTALL DEVICEs Nvidia DRIVERs

```sh

sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-utils-535
sudo reboot

nvidia-smi
```