# Pangolin 🦎

Pangolin is a versatile Python SDK designed to simplify interactions with various systems and services, providing a unified, extensible interface for different types of operations.

## 🌟 Project Overview

Pangolin offers a comprehensive set of tools for:
- Database Interactions
- API Connections
- SSH Operations
- Command Execution
- Data Validation

## 🚀 Features

### Core Components
- **Unified Engine Architecture**
- **Flexible Configuration Management**
- **Comprehensive Error Handling**
- **Logging Support**

### Supported Integrations
- **Databases**: 
  - SQLite
  - PostgreSQL
  - MySQL
  - Oracle
  - Microsoft SQL Server

- **API Interactions**:
  - Multiple Authentication Methods
  - Flexible HTTP Verb Support
  - Advanced Request Handling

- **System Interactions**:
  - SSH Command Execution
  - Local Command Running

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip

### Install from Source
```bash
git clone https://github.com/manish59/Pangolin.git
cd Pangolin
pip install -e .
```

### Dependencies
```bash
pip install -r requirements.txt
```

## 🛠 Usage Examples

### Database Engine
```python
from pangolin.database import Engine

# Create database engine
db_engine = Engine(
    database_type='sqlite', 
    database='example.db'
)

# Setup connection
db_engine.setup()

# Execute query
results = db_engine.execute('SELECT * FROM users')
```

### API Engine
```python
from pangolin.api import APIEngine

# Create API engine
api_engine = APIEngine(
    base_url='https://api.example.com',
    auth_type='token',
    token='your_access_token'
)

# Execute request
response = api_engine.execute('/users', method='GET')
```

### SSH Engine
```python
from pangolin.ssh import SSHClient

# Create SSH client
ssh_client = SSHClient(
    hostname='example.com',
    username='user',
    private_key='/path/to/private/key'
)

# Execute remote command
stdout, stderr, status = ssh_client.execute('ls -l')
```

## 🔐 Authentication Support

Pangolin supports multiple authentication methods:
- Basic Authentication
- Token-based Authentication
- API Key Authentication
- OAuth 2.0
- Custom Header Authentication

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the Apache License, Version 2.0. See `LICENSE` for more information.

### Apache 2.0 License Summary
- You can use, modify, and distribute the software
- You must include a copy of the license
- Provide attribution
- State changes if you modify the code
- No warranty is provided

## 📞 Contact

Manish Kumar Bobbili
- GitHub: [@manish59](https://github.com/manish59)
- Project Link: [https://github.com/manish59/Pangolin](https://github.com/manish59/Pangolin)

## 🙏 Acknowledgements
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Requests](https://docs.python-requests.org/)
- [Paramiko](https://www.paramiko.org/)
