# SD-Host Architecture

## Overview

SD-Host follows a layered architecture pattern that promotes separation of concerns, maintainability, and testability.

## Architecture Layers

```
┌─────────────────────────────────────┐
│              Interfaces             │
│  ┌─────────────┐  ┌─────────────┐   │
│  │     API     │  │     CLI     │   │
│  │   (HTTP)    │  │ (Commands)  │   │
│  └─────────────┘  └─────────────┘   │
└─────────────┬───────────┬───────────┘
              │           │
              └─────┬─────┘
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
**Purpose**: Command-line interface
- Command parsing and execution
- Service management utilities
- Administrative tools

**Dependencies**: `core/`

## Directory Structure

```
src/
├── api/                    # HTTP Interface Layer
│   ├── main.py            # FastAPI application
│   ├── models.py          # API route handlers for models
│   ├── model_actions.py   # API route handlers for model actions
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

1. **Separation of Concerns**: Each layer has a single, well-defined responsibility
2. **Dependency Direction**: Dependencies flow inward (interfaces → core → models)
3. **Testability**: Each layer can be tested independently
4. **Maintainability**: Changes in one layer don't cascade to others
5. **Flexibility**: Multiple interfaces (API, CLI) can share the same business logic
6. **Scalability**: Easy to add new interfaces or modify existing ones

## Development Guidelines

1. **Layer Independence**: Higher layers can depend on lower layers, but not vice versa
2. **Interface Contracts**: Define clear interfaces between layers
3. **Business Logic Isolation**: Keep business rules in the core layer, not in interfaces
4. **Data Access Abstraction**: Use repository patterns to abstract database access
5. **Configuration Management**: Centralize configuration in the core layer

## Migration Plan

The current codebase has some legacy structures that will be gradually refactored:

1. **`services/`** → **`core/`**: Move business logic from services to core
2. **Route Handlers**: Keep thin, delegate to core services
3. **Database Models**: Ensure they only handle data concerns
4. **CLI Tools**: Ensure they use core services, not direct database access

This architecture ensures SD-Host remains maintainable and extensible as it grows.
