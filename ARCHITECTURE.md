# SD-Host Architecture

## Overview

SD-Host follows a layered architecture pattern that promotes separation of concerns, maintainability, and testability.

## Architecture Layers

The dependency chain follows: **CLI → API → Core → Models**

```
┌─────────────────────────────────────┐
│        Command Line Interface      │
│  ┌─────────────────────────────────┐ │
│  │             CLI                 │ │
│  │      (Management Tools)         │ │
│  └─────────────────────────────────┘ │
└─────────────────┬───────────────────┘
                  │ HTTP requests
                  ▼
┌─────────────────────────────────────┐
│           HTTP Interface            │
│  ┌─────────────────────────────────┐ │
│  │             API                 │ │
│  │    (REST Endpoints & Tasks)     │ │
│  └─────────────────────────────────┘ │
└─────────────────┬───────────────────┘
                  │ depends on
                  ▼
┌─────────────────────────────────────┐
│           Business Logic            │
│  ┌─────────────────────────────────┐ │
│  │             Core                │ │
│  │  (Services & Domain Logic)      │ │
│  └─────────────────────────────────┘ │
└─────────────────┬───────────────────┘
                  │ depends on
                  ▼
┌─────────────────────────────────────┐
│           Data Access               │
│  ┌─────────────────────────────────┐ │
│  │            Models               │ │
│  │   (Database & Persistence)     │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Why CLI → API?

This design ensures:
- **Single GPU Process**: Only the API service accesses GPU resources
- **Centralized Task Management**: All operations go through the HTTP service
- **Consistent State**: Shared database and configuration through single service
- **Remote Management**: CLI can manage services on different machines
- **Resource Safety**: Prevents multiple processes from competing for GPU/model resources
│  │   (Database & Persistence)     │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Models Layer (`src/models/`)
**Purpose**: Data access and persistence
- Database models and ORM definitions
- Data validation and serialization
- Database connection management
- Repository patterns

**Dependencies**: None (base layer)

### 2. Core Layer (`src/core/`)
**Purpose**: Business logic and domain services
- Business rules and domain logic
- Service orchestration
- Application configuration
- Cross-cutting concerns (logging, etc.)

**Dependencies**: `models/`

### 3. Interface Layers

#### API Layer (`src/api/`)
**Purpose**: HTTP interface and REST endpoints
- FastAPI application and routing
- Request/response handling
- HTTP middleware
- API documentation

**Dependencies**: `core/`

#### CLI Layer (`src/cli/`)
**Purpose**: Command-line interface via HTTP API
- Command parsing and execution
- Service management utilities  
- Administrative tools
- **HTTP client**: Makes REST calls to API service

**Dependencies**: API service (via HTTP calls)
**Note**: CLI does not directly access Core or Models layers. Instead, it communicates with the running API service via HTTP requests. This design ensures:
- Single point of access to GPU resources
- No process conflicts or resource contention
- Consistent business logic execution
- Service-oriented architecture benefits

## Directory Structure

```
src/
├── api/                    # HTTP Interface Layer
│   ├── main.py            # FastAPI application
│   ├── models.py          # API route handlers for models and model actions
│   └── __init__.py
├── cli/                   # CLI Interface Layer
│   ├── sdh.py            # CLI implementation
│   └── README.md
├── core/                  # Business Logic Layer
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection and setup
│   └── __init__.py
├── models/                # Data Access Layer
│   ├── __init__.py       # Model definitions
│   └── ...               # Additional model files
├── services/              # Legacy (to be refactored into core/)
└── utils/                 # Shared utilities
```

## Benefits of This Architecture

1. **GPU Resource Safety**: Single API process owns GPU access, preventing:
   - Multiple processes competing for GPU memory
   - Model loading conflicts
   - CUDA context conflicts
   - Resource exhaustion issues

2. **Service-Oriented Design**: CLI communicates with API via HTTP, enabling:
   - Remote management capabilities
   - Process isolation and safety
   - Stateless CLI operations
   - Service restart without affecting CLI tools

3. **Separation of Concerns**: Each layer has a single, well-defined responsibility
4. **Dependency Direction**: Code dependencies flow inward (API → core → models)
5. **Testability**: Each layer can be tested independently
6. **Maintainability**: Changes in one layer don't cascade to others
7. **Scalability**: Easy to add new interfaces or modify existing ones
8. **Consistency**: All operations go through the same business logic in the API service
9. **Centralized State**: Single source of truth for models, tasks, and configuration

## Development Guidelines

1. **Layer Independence**: Higher layers can depend on lower layers, but not vice versa
2. **Interface Contracts**: Define clear interfaces between layers
3. **Business Logic Isolation**: Keep business rules in the core layer, not in interfaces
4. **Data Access Abstraction**: Use repository patterns to abstract database access
5. **Configuration Management**: Centralize configuration in the core layer
6. **CLI-API Communication**: CLI should only communicate with API via HTTP calls, never direct imports

## CLI-API Design Rationale

### Why CLI Uses HTTP Instead of Direct Imports

**Problem**: GPU resource contention and process conflicts
- Multiple processes accessing GPU simultaneously causes errors
- Direct imports would create separate process instances
- Shared state management becomes complex

**Solution**: Service-oriented CLI design
- Single API service manages all GPU access
- CLI acts as HTTP client to running API service
- Centralized resource management and state

**Benefits**:
- **Resource Safety**: Only one process controls GPU
- **State Consistency**: Single source of truth for application state  
- **Process Isolation**: CLI and API can run independently
- **Service Reusability**: Multiple CLI instances can use same API service
- **Deployment Flexibility**: API and CLI can be on different machines

**Implementation**:
```python
# CLI makes HTTP calls, not direct imports
response = requests.get(f"{api_base}/api/models")

# NOT: from core.services import model_service
```

## Migration Plan

The current codebase has some legacy structures that will be gradually refactored:

1. **`services/`** → **`core/`**: Move business logic from services to core
2. **Route Handlers**: Keep thin, delegate to core services
3. **Database Models**: Ensure they only handle data concerns
4. **CLI Tools**: Ensure they use core services, not direct database access

This architecture ensures SD-Host remains maintainable and extensible as it grows.
