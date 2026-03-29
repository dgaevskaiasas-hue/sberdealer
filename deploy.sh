#!/bin/bash
# SberDealer Backend — Full Deploy Script for Ubuntu 24.04
# Run as: bash deploy.sh
set -e

SERVER_IP="203.161.56.96"
APP_DIR="/opt/sberdealer"
DB_NAME="sber_dealer"
DB_USER="sberdealer"
DB_PASS="SberDealer2026!"
REPO_URL="https://github.com/kheladzedev/SberDealerServer.git"
BRANCH="Dottys"

echo "=== 1. Обновляем систему ==="
apt-get update -y && apt-get upgrade -y

echo "=== 2. Устанавливаем зависимости ==="
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib git nginx curl

echo "=== 3. Настраиваем PostgreSQL ==="
systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

echo "=== 4. Клонируем репозиторий ==="
rm -rf $APP_DIR
git clone -b $BRANCH $REPO_URL $APP_DIR
cd $APP_DIR

echo "=== 5. Виртуальное окружение и зависимости ==="
python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

echo "=== 6. Создаём .env ==="
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASS@localhost/$DB_NAME
SYNC_DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
GIGACHAT_AUTH_KEY=MDE5ZDEyMzYtOTM3MC03ZDc5LTgxNzEtZTI5YmNhMDBiZTg0OjIyNjUyMTA4LWI1OGUtNGIxMy1iZDk1LTVlNjhkZDI1MzczNA==
REDIS_URL=redis://localhost:6379/0
EOF

echo "=== 7. Применяем миграции ==="
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/001_init.sql
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/002_auth_registration.sql
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/003_per_user_metrics.sql
PGPASSWORD=$DB_PASS psql -h localhost -U $DB_USER -d $DB_NAME -f migrations/004_learning.sql

echo "=== 8. Заполняем тестовые данные ==="
cd $APP_DIR
venv/bin/python seed/seed.py
venv/bin/python seed/seed_learning.py
venv/bin/python seed/seed_learning_content.py

echo "=== 9. Создаём systemd-сервис ==="
cat > /etc/systemd/system/sberdealer.service << EOF
[Unit]
Description=SberDealer FastAPI Backend
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sberdealer
systemctl start sberdealer

echo "=== 10. Настраиваем Nginx ==="
cat > /etc/nginx/sites-available/sberdealer << EOF
server {
    listen 80;
    server_name $SERVER_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/sberdealer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
systemctl enable nginx

echo ""
echo "✅ Деплой завершён!"
echo "   API: http://$SERVER_IP/health"
echo "   Docs: http://$SERVER_IP/docs"
