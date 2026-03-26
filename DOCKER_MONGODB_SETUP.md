# Docker MongoDB Setup Guide for ABFRL

## 🐳 Two Options for MongoDB with Docker

### **Option 1: MongoDB in Docker (Recommended for Development)**

MongoDB runs as a container alongside your FastAPI app. Perfect for local development!

### **Option 2: MongoDB Atlas (Cloud)**

Use cloud MongoDB while running FastAPI in Docker. Requires internet, but no local MongoDB.

---

## ✅ Option 1: MongoDB in Docker (Complete Setup)

### **Step 1: Update Environment Variables**

Your `.env` file already has MongoDB Docker credentials:

```bash
MONGO_USERNAME=abfrl_user
MONGO_PASSWORD=secure_password_change_me
MONGODB_DB_NAME=abfrl_fashion
```

**⚠️ For production, change the password!**

```bash
MONGO_PASSWORD=YourSecure@Password123
```

### **Step 2: Start Docker Containers**

```bash
# Navigate to backend folder
cd /Users/deveshs/Final-year-project/backend-finalyear-project

# Start both MongoDB and FastAPI containers
docker-compose up -d

# View logs
docker-compose logs -f
```

**What happens:**

- ✅ MongoDB container starts on port 27017
- ✅ FastAPI container starts on port 8000
- ✅ Database `abfrl_fashion` is created automatically
- ✅ Collections (users, products, orders, etc.) are created
- ✅ Indexes are created for performance

### **Step 3: Verify Connection**

```bash
# Check containers are running
docker-compose ps

# Test MongoDB connection
docker exec abfrl-mongodb mongosh -u abfrl_user -p secure_password_change_me --authenticationDatabase admin --eval "db.adminCommand('ping')"
```

Expected output:

```
{ ok: 1 }
```

### **Step 4: Load Sample Data**

```bash
# Access the app container
docker exec -it retail-sales-agent bash

# Run the sample data loader
python load_sample_data.py

# Exit container
exit
```

---

## 🌐 Option 2: MongoDB Atlas with Docker FastAPI

### **Step 1: Get MongoDB Atlas Connection String**

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create cluster and database user (see MONGODB_SETUP.md)
3. Copy the connection string from "Connect" → "Drivers" → "Python"

Example:

```
mongodb+srv://abfrl_admin:YourPassword@abfrl-cluster.mongodb.net/?retryWrites=true&w=majority
```

### **Step 2: Update .env for Atlas**

Instead of Docker MongoDB variables, use:

```bash
# Comment out Docker variables:
# MONGO_USERNAME=abfrl_user
# MONGO_PASSWORD=secure_password_change_me

# Add Atlas connection:
MONGODB_URI=mongodb+srv://abfrl_admin:YourPassword@abfrl-cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=abfrl_fashion
```

### **Step 3: Update docker-compose.yml (Atlas Mode)**

Edit `docker-compose.yml` and **remove the MongoDB service**:

```yaml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: retail-sales-agent
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL}
      - MONGODB_URI=${MONGODB_URI}
      - MONGODB_DB_NAME=${MONGODB_DB_NAME}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### **Step 4: Start Docker (Atlas Mode)**

```bash
docker-compose up -d
```

---

## 🔧 Useful Docker Commands

| Command                                   | What it does                   |
| ----------------------------------------- | ------------------------------ |
| `docker-compose up -d`                    | Start containers in background |
| `docker-compose down`                     | Stop and remove containers     |
| `docker-compose logs -f`                  | Show live logs                 |
| `docker-compose ps`                       | Show running containers        |
| `docker exec -it retail-sales-agent bash` | Enter app container shell      |
| `docker exec -it abfrl-mongodb mongosh`   | Enter MongoDB shell            |

### **MongoDB Shell Commands (Inside Container)**

```bash
# Enter MongoDB shell
docker exec -it abfrl-mongodb mongosh -u abfrl_user -p secure_password_change_me --authenticationDatabase admin

# Inside mongosh:
use abfrl_fashion                    # Switch database
db.products.find()                   # View all products
db.products.countDocuments()         # Count documents
db.collections()                     # List all collections
exit                                 # Exit shell
```

---

## 📊 Docker Network Architecture

```
┌─────────────────────────────────────────────────┐
│            Docker Compose Network                │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────┐    ┌──────────────────┐  │
│  │  FastAPI App     │    │  MongoDB         │  │
│  │  Port 8000       │◄──►│  Port 27017      │  │
│  │ retail-sales-    │    │ abfrl-mongodb    │  │
│  │ agent            │    │                  │  │
│  └──────────────────┘    └──────────────────┘  │
│                                                  │
│  Network: retail-network                         │
│  Volume: mongodb_data (persistent)               │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ Troubleshooting

### **Error: "Cannot connect to MongoDB"**

```bash
# Check if MongoDB container is running
docker-compose ps

# Check logs
docker-compose logs mongodb

# Restart containers
docker-compose restart
```

### **Port Already in Use (8000 or 27017)**

```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Map container 8000 to host 8001
```

### **MongoDB Authentication Failed**

- Verify `MONGO_USERNAME` and `MONGO_PASSWORD` in `.env`
- Restart containers: `docker-compose restart`
- Check init script ran: `docker-compose logs mongodb`

### **Data Won't Persist**

- Ensure `mongodb_data` volume exists
- Check volume permissions: `docker volume ls`
- Recreate volume: `docker-compose down -v && docker-compose up -d`

---

## 🚀 Production Deployment Checklist

- [ ] Change `MONGO_PASSWORD` to strong password
- [ ] Use MongoDB Atlas for production (more reliable)
- [ ] Add IP whitelisting in MongoDB Atlas
- [ ] Set `restart: always` for containers
- [ ] Use environment-specific `.env` files
- [ ] Add database backups
- [ ] Monitor container logs
- [ ] Use secrets management (Docker Secrets, Kubernetes Secrets)

---

## 📚 Quick Reference

**Local MongoDB in Docker:**

```bash
docker-compose up -d
```

**MongoDB Shell:**

```bash
docker exec -it abfrl-mongodb mongosh -u abfrl_user -p secure_password_change_me --authenticationDatabase admin
```

**View Logs:**

```bash
docker-compose logs -f app
docker-compose logs -f mongodb
```

**Stop Everything:**

```bash
docker-compose down
```

**Reset Database (⚠️ Deletes all data):**

```bash
docker-compose down -v
docker-compose up -d
```
