# Quick Start Guide

## 🚀 Start the Application (30 seconds)

```bash
docker-compose up --build
```

That's it! The application will:
- ✅ Start PostgreSQL database
- ✅ Run migrations
- ✅ Seed test data
- ✅ Start the API server

## 📍 Access Points

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 API Key

All endpoints require this header:
```
X-API-Key: your-secret-key
```

## 🎯 Test It Now

### Using Swagger UI (Recommended)
1. Open http://localhost:8000/docs
2. Click "Authorize" → Enter: `your-secret-key`
3. Try the endpoints!

### Using cURL
```bash
# Get all organizations
curl -H "X-API-Key: your-secret-key" http://localhost:8000/organizations

# Search by activity (includes children)
curl -H "X-API-Key: your-secret-key" \
  "http://localhost:8000/organizations?activity_id=1"

# Geo search (1km radius from Red Square)
curl -H "X-API-Key: your-secret-key" \
  "http://localhost:8000/organizations?lat=55.7539&lon=37.6208&radius=1000"
```

## 📊 Test Data

The database includes:
- **3 buildings** in Moscow
- **8 activities** (Food → Meat/Dairy, Automobiles → Trucks/Cars → Parts/Accessories)
- **5 organizations**

## 🛠️ Useful Commands

```bash
# View logs
make logs

# Stop services
make down

# Restart services
make restart

# Clean everything (remove containers and volumes)
make clean

# View all available commands
make help
```

## 🔧 Local Development

```bash
# Install dependencies
make install      # production only
make install-dev  # with dev tools

# Code quality
make format       # format with black
make lint         # lint with ruff
make check-types  # type check with mypy
```

## 📚 More Information

- [README.md](README.md) - Full documentation
- [EXAMPLES.md](EXAMPLES.md) - API usage examples
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Technical details

## ✅ Verify Installation

Run the test script:
```bash
chmod +x test_api.sh
./test_api.sh
```

## 🎓 Key Features to Try

1. **Hierarchical Search**: Search activity "Food" (id=1) returns all food-related organizations (meat, dairy, etc.)
2. **Geo Search**: Find organizations within radius or bounding box
3. **Combined Filters**: Mix activity, location, name, and building filters
4. **Auto Documentation**: Explore all endpoints in Swagger UI

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

**Database connection issues?**
```bash
# Check database is healthy
docker-compose ps

# View database logs
docker-compose logs db
```

**Need to reset data?**
```bash
docker-compose down -v
docker-compose up --build
```

---

**Need help?** Check the [README.md](README.md) or open an issue.
