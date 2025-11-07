# 🤿 Dive Analyzer - Codebase Architecture Overview

## 1. PROJECT STRUCTURE

### Tech Stack
- **Frontend Framework**: Streamlit (Python web framework)
- **Backend**: Python (no separate backend, monolithic structure)
- **Database**: SQLite (local)
- **Visualization**: Plotly (interactive charts), Folium (maps)
- **File Parsing**: FitParse (FIT format), XML parsing, custom parsers
- **Data Processing**: Pandas, NumPy

### Directory Structure
```
dive-analyzer/
├── app.py                          # Main entry point (home page)
├── config.py                       # Centralized configuration
├── database.py                     # SQLite CRUD operations (870 lines)
├── parser.py                       # Multi-format file parsing (500+ lines)
├── analyzer.py                     # Dive physics calculations (350+ lines)
├── visualizer.py                   # Plotly visualizations (300+ lines)
├── validation.py                   # File validation & sanitization
├── logger.py                       # Logging configuration
├── pages/
│   ├── 1_📤_Analyse.py            # Dive analysis page
│   ├── 2_📖_Journal.py            # Dive log journal page
│   └── 3_🗺️_Carte.py              # Interactive map page
├── tests/
│   ├── __init__.py
│   ├── test_validation.py         # 41 tests
│   ├── test_parser.py             # 55+ tests
│   └── test_database.py           # 60+ tests
├── requirements.txt               # Python dependencies
└── [Documentation files]
```

---

## 2. DATA MODELS FOR DIVE LOGS

### Core Data Entities

#### Dive Profile Data (DataFrame format after parsing)
Raw data extracted from dive computer files:
```python
DataFrame columns:
- temps_secondes: float          # Elapsed time since dive start
- profondeur_metres: float       # Water depth in meters
- temperature_celsius: float     # Water temperature
- pression_bouteille_bar: float  # Tank pressure (if available)
```

#### Calculated Metrics (stored in dives table)
```python
{
    'profondeur_max': float,           # Maximum depth (meters)
    'duree_minutes': float,            # Total duration
    'temperature_min': float,          # Minimum water temperature
    'sac': float,                      # Surface Air Consumption (L/min)
    'temps_fond_minutes': float,       # Bottom time (minutes)
    'vitesse_remontee_max': float,     # Maximum ascent speed (m/min)
}
```

#### Dive Annotations (user input)
```python
{
    'date': str,                       # Dive datetime
    'site_nom': str,                   # Dive site name
    'buddy_nom': str,                  # Dive buddy name (optional)
    'dive_type': str,                  # 'exploration', 'formation', 'technique'
    'rating': int,                     # 1-5 star rating
    'notes': str,                      # Free text notes
    'houle': str,                      # 'aucune', 'faible', 'moyenne', 'forte'
    'visibilite_metres': int,          # Water visibility
    'courant': str,                    # 'aucun', 'faible', 'moyen', 'fort'
    'tags': List[str],                 # Custom tags ('Épave', 'Grotte', etc.)
}
```

#### File Reference
```python
{
    'fichier_original_nom': str,       # Original filename
    'fichier_original_path': str,      # Full path to stored file
}
```

---

## 3. DATABASE SCHEMA

### SQLite Structure (6 tables)

#### Table: `dives` (Main table)
```sql
CREATE TABLE dives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Dive metadata
    date TEXT NOT NULL,
    site_id INTEGER NOT NULL,
    buddy_id INTEGER,
    dive_type TEXT CHECK(dive_type IN ('exploration', 'formation', 'technique')),
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    notes TEXT,
    
    -- Environmental conditions
    houle TEXT CHECK(houle IN ('aucune', 'faible', 'moyenne', 'forte')),
    visibilite_metres INTEGER,
    courant TEXT CHECK(courant IN ('aucun', 'faible', 'moyen', 'fort')),
    
    -- Technical metrics
    profondeur_max REAL,
    duree_minutes REAL,
    temperature_min REAL,
    sac REAL,
    temps_fond_minutes REAL,
    vitesse_remontee_max REAL,
    
    -- File reference
    fichier_original_nom TEXT,
    fichier_original_path TEXT,
    
    -- Foreign keys
    FOREIGN KEY (site_id) REFERENCES sites(id),
    FOREIGN KEY (buddy_id) REFERENCES buddies(id)
)
```

**Indexes**:
- `idx_dives_date` - ON dives(date DESC) - Fast date sorting
- `idx_dives_site_id` - ON dives(site_id) - Fast JOINs with sites
- `idx_dives_rating` - ON dives(rating DESC) - Fast rating filters
- `idx_dives_date_site` - ON dives(date DESC, site_id) - Combined queries

#### Table: `sites`
```sql
CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    pays TEXT,
    coordonnees_gps TEXT  -- Format: "latitude,longitude"
)
```

#### Table: `buddies`
```sql
CREATE TABLE buddies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    niveau_certification TEXT  -- e.g., "Niveau 2 FFESSM"
)
```

#### Table: `tags`
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    categorie TEXT  -- Optional category
)
```

#### Table: `dive_tags` (Many-to-many relationship)
```sql
CREATE TABLE dive_tags (
    dive_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (dive_id, tag_id),
    FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
)
```

#### Table: `cached_dive_data` (Performance optimization - Phase 2)
```sql
CREATE TABLE cached_dive_data (
    dive_id INTEGER PRIMARY KEY,
    cached_dataframe BLOB NOT NULL,  -- Pickled DataFrame
    cache_timestamp TEXT NOT NULL,
    file_hash TEXT,
    FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE
)
```

**Location**: `~/dive-analyzer/dive_log.db`

---

## 4. PAGES AND COMPONENTS

### Page 1: 📤 Analyse (1_📤_Analyse.py)
**Purpose**: Upload and analyze dive files

**Features**:
- File upload (supports: .fit, .xml, .uddf, .dl7)
- File validation (extension, size, magic bytes)
- Dive profile parsing
- Dashboard KPIs (depth, duration, SAC, temp, etc.)
- Interactive Plotly profile graph
- Safety alerts (ascent speed, decompression)
- Nitrogen saturation analysis (Bühlmann ZH-L16C)
- Safety stop detection
- Annotation form with dive conditions
- Save to journal (database)

**Key Sections**:
1. File uploader with validation
2. File metrics display
3. Profile visualization
4. Physics calculations display
5. Annotation form
6. Save button

### Page 2: 📖 Journal (2_📖_Journal.py)
**Purpose**: Browse, filter, and manage dive logs

**Features**:
- Global statistics (total dives, max depth, total time, median SAC, avg rating)
- Advanced filtering:
  - By site (multiselect)
  - By date range
  - By depth range
  - By rating
  - By dive type
- Search by tags
- Sortable dive list
- Detailed dive view (read-only information)
- Edit annotations (site, buddy, type, conditions, notes)
- View original profile (reload from file)
- Delete dives
- Dynamic tag management

**Key Sections**:
1. Global statistics metrics
2. Filter controls
3. Filtered dive list table
4. Dive detail tabs:
   - 📋 Information (read-only)
   - 📊 Profile Graph
   - ✏️ Edit form

### Page 3: 🗺️ Carte (3_🗺️_Carte.py)
**Purpose**: Visualize dive sites on interactive map

**Features**:
- Interactive Folium map with OpenStreetMap
- Colored markers by dive frequency:
  - 🔵 Blue: 1-4 dives
  - 🟠 Orange: 5-9 dives
  - 🔴 Red: 10+ dives
- Popup information per site:
  - Number of dives
  - Max/average depth
  - Temperature, SAC, rating
  - First/last dive dates
- Global statistics:
  - Total sites
  - Total dives
  - Geolocalized sites
  - Countries visited
- GPS coordinate editing
- Coordinate validation

### Home Page (app.py)
**Purpose**: Navigation hub

**Features**:
- Navigation buttons to Analysis, Journal, Map
- Feature descriptions
- Getting started info

---

## 5. CORE MODULES

### config.py (187 lines)
**Configuration Management** (Singleton pattern)

```python
Config class attributes:
├── Paths
│   ├── APP_DIR: ~/dive-analyzer
│   ├── UPLOADS_DIR, BACKUP_DIR
│   ├── DB_PATH, LOG_FILE
├── File Limits
│   ├── MAX_FILE_SIZE_MB: 50
│   └── ALLOWED_EXTENSIONS: {.fit, .xml, .uddf, .dl7}
├── Physics Parameters
│   ├── MAX_DEPTH_M: 200
│   ├── DEPTH_THRESHOLD_M: 3 (for bottom time)
│   ├── MAX_SAFE_ASCENT_SPEED_M_MIN: 10
│   ├── WARNING_ASCENT_SPEED_M_MIN: 15
│   └── Safety stop parameters
├── UI Settings
│   ├── DIVES_PER_PAGE: 25
│   └── DEFAULT_TANK_VOLUME_L: 12
├── Standard Tags: Épave, Grotte, Tombant, Nuit, etc.
└── Color Scheme: Safe (blue), Warning (orange), Danger (red)
```

**Key Methods**:
- `validate_depth()` - Check depth limits
- `get_ascent_speed_category()` - Categorize ascent speed
- `get_color_for_speed()` - Return color for visualization

### database.py (870 lines)
**Database CRUD Operations & Management**

**Core Functions**:
- `init_database()` - Initialize tables and indexes
- `get_connection()` - SQLite connection factory
- `insert_site()`, `insert_buddy()`, `insert_tag()` - Entity insertion
- `insert_dive()` - Complete dive insertion with related entities
- `get_all_dives()` - Retrieve all dives as DataFrame
- `get_dive_by_id()` - Full dive details
- `update_dive()` - Update annotations
- `delete_dive()` - Delete with cascade
- `get_all_tags()` - Retrieve unique tags
- `get_all_sites_with_stats()` - Sites with aggregated statistics
- `update_site_coordinates()` - Update GPS coordinates
- `save_dive_cache()` - Cache DataFrame (performance)
- `get_dive_cache()` - Retrieve cached DataFrame
- `invalidate_dive_cache()` - Clear cache entry
- `get_cache_stats()` - Cache performance metrics

**Key Features**:
- Foreign key constraints enabled
- Cascade deletion for data integrity
- Automatic site/buddy/tag creation (insert-or-get pattern)
- Many-to-many relationship handling
- DataFrame caching with pickle serialization
- Comprehensive logging

### parser.py (500+ lines)
**Multi-Format Dive File Parsing**

**Parser Architecture** (Strategy pattern):
```
BaseDiveParser (abstract)
├── FitParser         # Garmin FIT format
├── XmlParser         # Generic XML
├── UddfParser        # UDDF (Universal Dive Data Format)
└── DL7Parser         # OSTC proprietary format
```

**Main Function**:
- `parse_dive_file(uploaded_file)` - Auto-detect format and parse

**Features**:
- Automatic format detection (extension + magic bytes)
- Unified DataFrame output format
- Error handling and validation
- Automatic sorting by time
- Temperature/pressure/depth extraction
- Support for various field names (depth, profondeur, etc.)

**Supported Formats**:
| Format | Extension | Source |
|--------|-----------|--------|
| FIT | .fit | Garmin Descent, Suunto EON |
| UDDF | .uddf, .xml | Subsurface, Universal format |
| XML | .xml | Various dive computers |
| DL7 | .dl7 | OSTC (HeinrichsWeikamp) |

### analyzer.py (350+ lines)
**Dive Physics Calculations**

**Calculation Functions**:
- `calculate_sac()` - Surface Air Consumption (L/min)
  - Mode A: Auto from pressure data
  - Mode B: Manual with user input
  - Weighted average pressure calculation
- `calculate_average_pressure()` - Time-weighted pressure integration
- `calculate_nitrogen_saturation()` - Bühlmann ZH-L16C model
  - Compartment half-times
  - Load/unload functions
  - Gradient factors
- `calculate_decompression_required()` - Check if safety stops needed
- `detect_rapid_descent()` - Ascent speed violations
- `calculate_ascent_time()` - Decompression time estimation

**Advanced Features**:
- Continuous integration for pressure averaging
- Support for multiple tank sizes
- Nitrogen absorption/release modeling
- Safety margin calculations

### visualizer.py (300+ lines)
**Interactive Visualizations**

**Plotly Graphs**:
- `create_dive_profile()` - Main depth/time graph
  - Color-coded ascent speed zones
  - Temperature overlay
  - Safety stop annotations
  - Time axis in minutes/seconds
- `create_saturation_plot()` - Nitrogen saturation levels
  - Per-compartment visualization
  - Gradient factor lines
  - Safety margins

**Utilities**:
- `calculate_ascent_speed()` - Speed between measurement points
- `detect_safety_stops()` - Identify decompression stops
- Color mapping for safety zones

**Interactive Features**:
- Hover tooltips with values
- Zoom and pan controls
- Legend toggling
- Responsive sizing

### validation.py (232 lines)
**File Upload Security**

**Validation Functions**:
- `validate_file_extension()` - Check allowed formats
- `validate_file_size()` - Check size limits (max 50MB)
- `validate_file_content()` - Magic bytes verification
  - FIT: `0x0e10`, `0x0e20`
  - XML: `<?xml`, `<uddf`
  - Detects malicious file renaming
- `validate_uploaded_file()` - Combined validation
- `sanitize_filename()` - Path traversal prevention

**Security Features**:
- Extension whitelist
- File size limits
- Magic byte verification
- Filename sanitization
- Path traversal prevention

### logger.py
**Logging Configuration**

Features:
- Rotating file handlers
- Structured logging
- Module-level loggers
- Log file: `~/dive-analyzer/dive_analyzer.log`

---

## 6. SUPPORTED FILE FORMATS

### FIT Format (Garmin)
- Used by: Garmin Descent, Suunto EON
- Extension: `.fit`
- Parser: FitParser (FitParse library)
- Data: Depth, temperature, pressure, timestamp

### UDDF Format (Universal)
- Used by: Subsurface, many dive computers
- Extension: `.uddf`, `.xml`
- Parser: UddfParser (XML-based)
- Specification: ISO 17185

### XML Format (Generic)
- Used by: Various dive computers
- Extension: `.xml`
- Parser: XmlParser (ElementTree)

### DL7 Format (OSTC)
- Used by: OSTC computers
- Extension: `.dl7`
- Parser: DL7Parser (binary format)
- Proprietary HeinrichsWeikamp format

---

## 7. SERVICES & CALCULATIONS

### Physics Calculations Services
1. **SAC Calculation** - Air consumption rate
2. **Nitrogen Saturation** - Decompression modeling
3. **Ascent Speed Analysis** - Safety monitoring
4. **Safety Stop Detection** - Automatic detection
5. **Decompression Requirements** - Safety assessment

### Data Services
1. **File Parsing** - Multi-format support
2. **Database CRUD** - Local SQLite persistence
3. **Caching** - DataFrame pickle caching
4. **File Validation** - Security checks

### Visualization Services
1. **Dive Profile Plotting** - Interactive graphs
2. **Map Rendering** - Site visualization
3. **Statistics Aggregation** - Summary metrics

---

## 8. TESTING INFRASTRUCTURE (Phase 2)

### Test Suites

#### test_validation.py (41 tests)
- Extension validation (6 tests)
- File size validation (6 tests)
- Content validation with magic bytes (7 tests)
- Filename sanitization (10 tests)
- Complete file validation (7 tests)
- Magic bytes structure (4 tests)

#### test_parser.py (55+ tests)
- BaseDiveParser abstract class
- FIT file parsing with various models
- XML/UDDF parsing with field variations
- DL7 proprietary format parsing
- Auto-format detection
- Error handling and edge cases
- Missing field handling

#### test_database.py (60+ tests)
- Connection management
- Database initialization
- CRUD operations for all entities
- Many-to-many relationships
- Cascade deletion
- Data integrity constraints
- Transaction handling

**Coverage**: > 80% across all modules

**Execution**:
```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov               # With coverage report
pytest tests/test_database.py      # Single test file
```

---

## 9. PERFORMANCE OPTIMIZATIONS (Phase 2)

### Database Indexes
- Date-based sorting (idx_dives_date)
- Site filtering (idx_dives_site_id)
- Rating filtering (idx_dives_rating)
- Combined queries (idx_dives_date_site)

### Caching Layer
- DataFrame caching in `cached_dive_data` table
- Pickle serialization for efficiency
- Cache invalidation on dive updates
- Hit rate tracking

### Key Features
- Foreign key constraints for integrity
- Normalized schema (5 tables + cache)
- Indexed queries for fast filtering
- Lazy evaluation in Streamlit

---

## 10. CONFIGURATION & ENVIRONMENT

### Key Configuration Values
- **Max File Size**: 50 MB
- **Max Depth**: 200 m (validation)
- **Safe Ascent Speed**: 10 m/min
- **Warning Threshold**: 15 m/min
- **Default Tank Volume**: 12 L
- **Cache Expiration**: Manual invalidation

### Directory Structure
```
~/dive-analyzer/
├── dive_log.db              # SQLite database
├── dive_analyzer.log        # Application logs
├── uploads/                 # Uploaded dive files
└── backups/                 # Database backups
```

---

## 11. KEY FEATURES SUMMARY

### Phase 1 - Core Features
- Multi-format dive file support (FIT, UDDF, XML, DL7)
- Interactive dive profile visualization
- Comprehensive physics calculations
- Local SQLite dive journal
- Filtering and statistics
- Interactive site map (Folium)

### Phase 2 - Quality & Performance
- 150+ unit tests (>80% coverage)
- Database indexing for speed
- DataFrame caching system
- Security validation hardening
- Comprehensive documentation
- CONTRIBUTING guide

### Planned Features (Roadmap)
- PDF export
- Advanced statistics graphs
- Auto GPS import from FIT files
- Bluetooth dive computer support
- Multi-user mode
- Marine weather API integration
- Site clustering on map
- KML/GPX export

---

## 12. SECURITY FEATURES

### File Upload Security
- Magic byte verification
- Filename sanitization
- Path traversal prevention
- File size limits
- Extension whitelist
- Content type validation

### Data Protection
- Foreign key constraints
- Transaction rollback on errors
- Cascade deletion for referential integrity
- Input validation throughout

### Access Control
- Local database only (no authentication needed)
- File permission checks
- Safe string handling

---

## 13. DEPENDENCIES

### Python Packages (requirements.txt)
```
streamlit==1.40.0      # Web framework
plotly==5.18.0         # Interactive graphs
pandas==2.2.2          # Data manipulation
numpy==1.26.4          # Numerical computing
fitparse==1.2.0        # FIT file parsing
folium==0.14.0         # Map library
streamlit-folium==0.16.0  # Streamlit map integration
```

### Development Dependencies
- pytest - Unit testing
- pytest-cov - Coverage reporting

---

## 14. ENTRY POINTS & STARTUP

### Starting the Application
```bash
# Via shell script
./start.sh

# Or directly
streamlit run app.py
```

**Web Interface**: `http://localhost:8501`

### Page Navigation
1. **Home** (app.py) - Menu and introduction
2. **Analysis** (pages/1_📤_Analyse.py) - File upload & analysis
3. **Journal** (pages/2_📖_Journal.py) - Dive log browsing
4. **Map** (pages/3_🗺️_Carte.py) - Site visualization

---

## 15. ARCHITECTURE PATTERNS

### Design Patterns Used
1. **Singleton** - Configuration (config.py)
2. **Strategy** - Parser plugins (FitParser, XmlParser, etc.)
3. **Factory** - Database connection
4. **MVC** - Streamlit page separation
5. **DTO** - Dive data dictionaries

### Code Organization
- **Separation of Concerns**: Each module has single responsibility
- **DRY Principle**: Generic `_insert_or_get_entity()` function
- **Configuration Management**: Centralized config.py
- **Error Handling**: Try-except with logging throughout
- **Type Hints**: Optional typing for better IDE support

---

## CONCLUSION

**Dive Analyzer** is a comprehensive Python/Streamlit application for analyzing and managing dive logs. It provides:

✅ Multi-format dive computer file support  
✅ Advanced physics calculations (SAC, nitrogen saturation, decompression)  
✅ Interactive visualization (Plotly, Folium)  
✅ Local SQLite database with indexed queries  
✅ Extensive unit tests (>80% coverage)  
✅ Performance optimization (caching, indexes)  
✅ Security hardening (file validation, input sanitization)  

The architecture is clean, modular, and well-documented, making it suitable for future enhancements and multi-user deployments.

