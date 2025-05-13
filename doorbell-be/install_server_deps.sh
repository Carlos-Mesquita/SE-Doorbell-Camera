#!/bin/bash
# Setup PostgreSQL

sudo apt update
sudo apt install -y postgresql

API_PASSWORD=$(openssl rand -base64 32)

sudo -u postgres psql -c "CREATE USER api WITH PASSWORD '$API_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE doorbell;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE apidb TO api;"

# Perms for alembic
sudo -u postgres psql -d doorbell -c "GRANT ALL ON SCHEMA public TO api;"
sudo -u postgres psql -d doorbell -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO api;"
sudo -u postgres psql -c "ALTER USER api CREATEDB;"

echo "PostgreSQL setup complete"
echo "Username: api"
echo "Database: doorbell"
echo "Password: $API_PASSWORD"

