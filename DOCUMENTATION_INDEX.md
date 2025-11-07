# 📚 Dive Analyzer - Documentation Index

## Complete Documentation Set for the Dive Analyzer Project

This index provides quick access to all comprehensive documentation about the Dive Analyzer codebase architecture, data models, and existing features.

---

## Documentation Files

### 1. **CODEBASE_OVERVIEW.md** (20 KB)
   **The Most Comprehensive Resource**
   
   Contains:
   - Detailed project structure and tech stack
   - Data models for dive logs (profiles, metrics, annotations)
   - Complete database schema (6 tables with SQL definitions)
   - Page-by-page feature breakdown
   - Core modules documentation (config, database, parser, analyzer, visualizer, validation)
   - Supported file formats (FIT, UDDF, XML, DL7)
   - Services and calculations
   - Testing infrastructure (150+ tests)
   - Performance optimizations
   - Security features
   - Design patterns used
   - Architecture overview
   
   **Use this when**: You need complete, detailed information about any aspect of the codebase

---

### 2. **QUICK_REFERENCE.md** (9 KB)
   **Fast Lookup Guide**
   
   Contains:
   - Project overview at a glance (table format)
   - File reference with line counts
   - Data model structure (dive record example)
   - Database tables summary
   - Key functions cheat sheet
   - Configuration quick reference
   - File format support table
   - Common workflows
   - Performance optimizations summary
   - Security features checklist
   - Development commands
   - Test coverage by module
   - Design patterns reference
   
   **Use this when**: You need quick facts, function signatures, or common operations

---

### 3. **ARCHITECTURE_DIAGRAM.txt** (19 KB)
   **Visual System Architecture**
   
   Contains:
   - ASCII architecture diagram showing layers and flow
   - Data flow diagrams (upload, browsing, mapping)
   - Supported file formats table
   - Physics calculations overview
   - Deployment architecture (current and future)
   - Testing coverage visualization
   - Key metrics summary
   
   **Use this when**: You need to understand system design visually or present architecture

---

## Quick Navigation Guide

### I need to understand...

#### The overall project structure
→ Start with **QUICK_REFERENCE.md** (Project Overview table)  
→ Then read **ARCHITECTURE_DIAGRAM.txt** (system overview)

#### Database design
→ Read **CODEBASE_OVERVIEW.md** Section 3 (Database Schema)  
→ Quick lookup: **QUICK_REFERENCE.md** (Database Tables Summary)

#### How to work with dives
→ **CODEBASE_OVERVIEW.md** Section 2 (Data Models)  
→ **QUICK_REFERENCE.md** (Dive Record Structure)

#### Available functions and modules
→ **QUICK_REFERENCE.md** (Key Functions Cheat Sheet)  
→ **CODEBASE_OVERVIEW.md** Section 5 (Core Modules)

#### The three main pages
→ **CODEBASE_OVERVIEW.md** Section 4 (Pages and Components)

#### How physics calculations work
→ **CODEBASE_OVERVIEW.md** Section 5 (analyzer.py subsection)  
→ **ARCHITECTURE_DIAGRAM.txt** (Physics Calculations section)

#### File format support
→ **QUICK_REFERENCE.md** (File Format Support table)  
→ **CODEBASE_OVERVIEW.md** Section 6 (Supported File Formats)

#### Security and validation
→ **CODEBASE_OVERVIEW.md** Section 12 (Security Features)  
→ **CODEBASE_OVERVIEW.md** Section 5 (validation.py module)

#### Testing approach
→ **CODEBASE_OVERVIEW.md** Section 8 (Testing Infrastructure)  
→ **QUICK_REFERENCE.md** (Test Coverage by Module)

#### Performance optimizations
→ **CODEBASE_OVERVIEW.md** Section 9 (Performance Optimizations)  
→ **QUICK_REFERENCE.md** (Performance Optimizations section)

---

## Key Facts Summary

| Aspect | Value |
|--------|-------|
| **Framework** | Streamlit (Python) |
| **Database** | SQLite (local) |
| **Total Code** | 2500+ lines |
| **Modules** | 7 core + 4 pages |
| **Tests** | 150+ (>80% coverage) |
| **Supported Formats** | FIT, UDDF, XML, DL7 |
| **Main Tables** | 6 (dives, sites, buddies, tags, dive_tags, cache) |
| **Database Indexes** | 4 (date, site_id, rating, composite) |
| **Visualizations** | Plotly (graphs), Folium (maps) |

---

## File Location Reference

```
/home/user/dive-analyzer/

Core Source Code:
├── app.py                          # Home page
├── config.py                       # Configuration (187 lines)
├── database.py                     # Database CRUD (870 lines)
├── parser.py                       # File parsing (500+ lines)
├── analyzer.py                     # Physics calculations (350+ lines)
├── visualizer.py                   # Visualizations (300+ lines)
├── validation.py                   # File validation (232 lines)
├── logger.py                       # Logging setup

Pages:
├── pages/1_📤_Analyse.py           # Upload & analyze
├── pages/2_📖_Journal.py           # Browse dive log
└── pages/3_🗺️_Carte.py            # Interactive map

Tests (150+ tests):
├── tests/test_validation.py        # 41 tests
├── tests/test_parser.py            # 55+ tests
└── tests/test_database.py          # 60+ tests

Documentation:
├── README.md                       # Main project README
├── CONTRIBUTING.md                 # Contributing guide
├── CODEBASE_OVERVIEW.md            # Detailed architecture (20 KB)
├── QUICK_REFERENCE.md              # Quick lookup (9 KB)
├── ARCHITECTURE_DIAGRAM.txt        # Visual diagrams (19 KB)
├── DOCUMENTATION_INDEX.md          # This file
├── PHASE2_COMPLETE.md              # Phase 2 completion report
├── AMELIORATIONS_PRIORITE1.md      # Planned improvements

Data:
├── dive_log.db                     # SQLite database
├── dive_analyzer.log               # Application logs
├── uploads/                        # Uploaded dive files
└── backups/                        # Database backups
```

---

## Understanding the Application Flow

### 1. **File Upload & Analysis**
   User uploads dive file → validation.py checks file → parser.py extracts data → 
   analyzer.py calculates physics → visualizer.py creates graphs → User annotates → 
   database.py saves to SQLite

### 2. **Dive Log Browsing**
   database.py retrieves dives → Filters applied → Statistics calculated → 
   Displayed in table → User can edit, delete, or view details

### 3. **Map Visualization**
   database.py gets all sites with stats → Folium creates map → Markers colored by 
   dive count → User can edit GPS coordinates

---

## Technology Stack Details

### Frontend
- **Streamlit**: Web framework for Python
- **Plotly**: Interactive charts and graphs
- **Folium**: Interactive maps (OpenStreetMap)
- **Pandas**: Data display and manipulation

### Backend
- **Python 3.8+**: Main language
- **SQLite**: Local database
- **NumPy**: Numerical calculations

### File Formats
- **FIT**: Garmin format (fitparse library)
- **UDDF**: Universal format (XML-based)
- **XML**: Generic format
- **DL7**: OSTC proprietary format

### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting

---

## Database Schema Summary

### Main Tables
- **dives**: 17 columns (metrics, conditions, annotations, file references)
- **sites**: Name, country, GPS coordinates
- **buddies**: Name, certification level
- **tags**: Names, categories
- **dive_tags**: Many-to-many relationships
- **cached_dive_data**: Performance optimization

### Relationships
- Dives → Sites (1:N, required)
- Dives → Buddies (1:N, optional)
- Dives ↔ Tags (M:N via dive_tags)
- Dives → Cache (1:1, optional)

### Indexes
- `idx_dives_date` - Fast date sorting
- `idx_dives_site_id` - Fast site filtering
- `idx_dives_rating` - Fast rating filtering
- `idx_dives_date_site` - Combined date + site queries

---

## Testing Overview

### Test Suites
- **test_validation.py**: 41 tests (~95% coverage)
  - File extension validation
  - File size validation
  - Magic byte content validation
  - Filename sanitization
  
- **test_parser.py**: 55+ tests (~85% coverage)
  - FIT parsing
  - UDDF/XML parsing
  - DL7 parsing
  - Auto-format detection
  
- **test_database.py**: 60+ tests (~90% coverage)
  - CRUD operations
  - Many-to-many relationships
  - Cascade deletion
  - Data integrity

### Running Tests
```bash
pytest tests/                    # All tests
pytest tests/ -v                 # Verbose
pytest tests/ --cov             # With coverage
pytest tests/test_database.py   # Single file
```

---

## Configuration & Customization

### Key Config Values (config.py)
```python
MAX_FILE_SIZE_MB = 50
MAX_DEPTH_M = 200.0
MAX_SAFE_ASCENT_SPEED_M_MIN = 10.0
WARNING_ASCENT_SPEED_M_MIN = 15.0
DEFAULT_TANK_VOLUME_L = 12.0
DIVES_PER_PAGE = 25
ALLOWED_EXTENSIONS = {'.fit', '.xml', '.uddf', '.dl7'}
```

### Standard Tags
Épave, Grotte, Tombant, Nuit, Dérivante, Formation, Technique, Faune, Flore, Photo, etc.

---

## Common Tasks & Where to Find Info

| Task | Document | Section |
|------|----------|---------|
| Understand database schema | CODEBASE_OVERVIEW | Section 3 |
| Find function signatures | QUICK_REFERENCE | Functions Cheat Sheet |
| Learn about data models | CODEBASE_OVERVIEW | Section 2 |
| See page features | CODEBASE_OVERVIEW | Section 4 |
| Understand physics | ARCHITECTURE_DIAGRAM | Physics Calculations |
| Check security features | CODEBASE_OVERVIEW | Section 12 |
| View test coverage | CODEBASE_OVERVIEW | Section 8 |
| Set up development | QUICK_REFERENCE | Development Commands |
| View configuration | QUICK_REFERENCE | Configuration Reference |

---

## Development Workflow

### Getting Started
1. Read **QUICK_REFERENCE.md** for overview
2. Review **ARCHITECTURE_DIAGRAM.txt** for visual understanding
3. Study **CODEBASE_OVERVIEW.md** sections relevant to your task

### Making Changes
1. Understand affected modules in **CODEBASE_OVERVIEW.md**
2. Review existing tests in **QUICK_REFERENCE.md** (Test Coverage)
3. Check configuration dependencies in **config.py**
4. Run relevant tests: `pytest tests/test_<module>.py`

### Adding Features
1. Plan database changes in **CODEBASE_OVERVIEW.md** (Section 3)
2. Review physics calculations in **analyzer.py** docs
3. Consider visualization in **visualizer.py** docs
4. Update tests accordingly

---

## Key Features at a Glance

### Current (Phase 2)
- 4 dive file format support
- Interactive profile visualization
- Advanced physics calculations
- Complete dive log management
- Interactive site mapping
- 150+ unit tests (>80% coverage)
- Database indexing & caching

### Planned (Phase 3)
- PDF export
- Advanced statistics
- Auto GPS import
- Bluetooth support
- Multi-user authentication
- Weather API integration
- Site clustering
- KML/GPX export

---

## Version & Status

- **Current Phase**: 2 (Complete)
- **Status**: Production-ready
- **Last Updated**: 2025-11-07
- **Total Tests**: 150+
- **Code Coverage**: >80%

---

## How to Use This Documentation

1. **First Time?** Start with **QUICK_REFERENCE.md**
2. **Need Details?** Go to **CODEBASE_OVERVIEW.md**
3. **Visual Learner?** Check **ARCHITECTURE_DIAGRAM.txt**
4. **Looking for Specific Info?** Use this index to navigate

---

## Additional Resources

- **README.md** - Project introduction
- **CONTRIBUTING.md** - Contribution guidelines
- **PHASE2_COMPLETE.md** - Phase 2 completion details
- **AMELIORATIONS_PRIORITE1.md** - Planned improvements
- **Source code** - See actual implementations

---

**Navigation Note**: All documentation files are in the project root at:
`/home/user/dive-analyzer/`

Start with your use case and navigate accordingly!
