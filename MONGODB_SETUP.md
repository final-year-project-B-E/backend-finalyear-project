# MongoDB Setup Guide for ABFRL Fashion Retail

## 📝 Step-by-Step Guide to Get MongoDB URI, Username & Password

### **Option 1: MongoDB Atlas (Cloud - Recommended for Production)**

#### 1. Create Free MongoDB Atlas Account

- Go to https://www.mongodb.com/cloud/atlas
- Click **"Sign up"** or **"Start free"**
- Create account with email
- Verify email

#### 2. Create a Project

- Once logged in, click **"Create a project"**
- Name it: `ABFRL-Fashion-Retail`
- Click **"Next"** → **"Create Project"**

#### 3. Create a Cluster (Database)

- Click **"Build a Database"**
- Choose **"Free"** tier (0.5GB storage, perfect for development)
- Select your region (closest to you)
- Choose cluster name: `abfrl-cluster`
- Click **"Create"** (takes 1-3 minutes)

#### 4. Create Database User (USERNAME & PASSWORD)

- Once cluster is ready, click **"Database Access"** (left sidebar)
- Click **"Add Database User"**
- **Username**: `abfrl_admin` (or your choice)
- **Password**: Click "Autogenerate Secure Password" or create one
  - **Example password**: `Secure#Pass123!` (save this!)
- **Built-in Role**: Select **"Atlas Admin"**
- Click **"Add User"**

#### 5. Allow Network Access

- Go to **"Network Access"** (left sidebar)
- Click **"Add IP Address"**
- Select **"Allow access from anywhere"** (0.0.0.0/0) for development
  - ⚠️ For production, add specific IPs
- Click **"Confirm"**

#### 6. Get Your Connection String (URI)

- Go to **"Databases"** → **"Database Deployments"**
- Click **"Connect"** button on your cluster
- Choose **"Drivers"** → **"Python"** → **"PyMongo"**
- **Copy the connection string**

The URI will look like:

```
mongodb+srv://abfrl_admin:Secure#Pass123!@abfrl-cluster.mongodb.net/?retryWrites=true&w=majority
```

⚠️ **IMPORTANT**: The URI contains your PASSWORD in plain text. Keep it secure!

---

### **Option 2: Local MongoDB (Development)**

#### 1. Install MongoDB Community Edition

**Mac (using Homebrew):**

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows:**

- Download from https://www.mongodb.com/try/download/community
- Run installer and follow prompts
- MongoDB runs as a Windows service

**Linux (Ubuntu):**

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

#### 2. For Local MongoDB

- **Username**: `abfrl_user` (optional for local)
- **Password**: `password123` (optional for local)
- **URI**: `mongodb://localhost:27017/?retryWrites=true&w=majority`

---

## 🔧 Configure Your ABFRL Backend

### 1. Install Dependencies

```bash
cd /Users/deveshs/Final-year-project/backend-finalyear-project
pip install -r requirements.txt
```

### 2. Create `.env` File

Copy `.env.example` and create `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
MONGODB_URI=mongodb+srv://abfrl_admin:YOUR_PASSWORD@abfrl-cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=abfrl_fashion
```

### 3. Verify Connection

Run this Python script to test connection:

```python
from dotenv import load_dotenv
from database import Database

load_dotenv()
db = Database()
print("✓ Connected to MongoDB successfully!")
```

### 4. Load Sample Data

Run the sample products script:

```bash
python add_sample_products.py
```

---

## 📊 MongoDB Collections Structure

Your database will have these collections:

| Collection      | Purpose                      |
| --------------- | ---------------------------- |
| `users`         | Customer accounts & profiles |
| `products`      | Fashion items catalog        |
| `carts`         | Shopping carts (by user_id)  |
| `orders`        | Order records                |
| `order_items`   | Items within orders          |
| `chat_sessions` | Chat conversation sessions   |
| `chat_messages` | Individual chat messages     |
| `agent_tasks`   | AI agent task tracking       |

---

## 🔐 Security Best Practices

1. **Never commit `.env` to git**

   ```bash
   echo ".env" >> .gitignore
   ```

2. **Rotate passwords regularly**
   - In Atlas: Database Access → Edit User

3. **Use strong passwords**
   - Min 8 characters, mix of upper/lowercase, numbers, symbols

4. **Restrict IP access in production**
   - Network Access → Edit allowed IPs → Add your server IPs only

5. **Use environment variables**
   - Never hardcode credentials in code

---

## 🚀 Deployment Environment Variables

When deploying to production (e.g., Heroku, Railway, Docker):

```bash
# Set environment variables
export MONGODB_URI="mongodb+srv://abfrl_admin:password@abfrl-cluster.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DB_NAME="abfrl_fashion"
```

Or in your hosting platform's dashboard (Heroku Config Vars, etc.)

---

## 🆘 Troubleshooting

### Connection Error: "dns: name 'x.mongodb.net' not known"

- Check internet connection
- Verify cluster is created in MongoDB Atlas
- Ensure IP is whitelisted

### Error: "Invalid username/password"

- Double-check username and password match exactly
- Check for extra spaces
- Regenerate password if forgotten

### 403 Forbidden Error

- Enable network access for your IP (0.0.0.0/0 for dev)
- Check user role is "Atlas Admin"

---

## 📞 Useful MongoDB Atlas Links

- [MongoDB Atlas Home](https://cloud.mongodb.com)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Query Language](https://docs.mongodb.com/manual/crud/)
