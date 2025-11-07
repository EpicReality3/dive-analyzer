# 🤿 Dive Analyzer - Quick Reference Guide

## Project Overview at a Glance

| Aspect | Details |
|--------|---------|
| **Framework** | Streamlit (Python web framework) |
| **Database** | SQLite (local, ~/dive-analyzer/dive_log.db) |
| **Main Language** | Python 3.8+ |
| **Total Lines of Code** | 2500+ (core modules) |
| **Unit Tests** | 150+ (>80% coverage) |
| **Supported Formats** | FIT, UDDF, XML, DL7 |
| **Entry Point** | `streamlit run app.py` |
| **Web URL** | http://localhost:8501 |

---

## Quick File Reference

### Core Modules
```
database.py     (870 lines)  → SQLite CRUD, caching, statistics
parser.py       (500 lines)  → Multi-format file parsing
analyzer.py     (350 lines)  → Physics calculations (SAC, N₂ saturation)
visualizer.py   (300 lines)  → Plotly interactive graphs
validation.py   (232 lines)  → File security validation
config.py       (187 lines)  → Centralized configuration
logger.py       (~100 lines) → Logging setup
```

### Pages (Streamlit)
```
app.py                     → Home navigation page
pages/1_📤_Analyse.py      → Upload & analyze dive files
pages/2_📖_Journal.py      → Browse & filter dive log
pages/3_🗺️_Carte.py        → Interactive map visualization
```

### Tests (150+ tests total)
```
tests/test_validation.py   → 41 tests (file validation)
tests/test_parser.py       → 55+ tests (format parsing)
tests/test_database.py     → 60+ tests (CRUD operations)
```

---

## Data Model at a Glance

### Dive Record Structure
```python
{
    'id': int,
    'date': '2025-11-02 14:30',
    'site': 'Port-Cros',
    'buddy': 'Marie',
    'profondeur_max': 42.3,        # max depth (m)
    'duree_minutes': 40.0,         # duration (min)
    'temperature_min': 16.2,       # min temp (C)
    'sac': 14.5,                   # air consumption (L/min)
    'temps_fond_minutes': 35.2,    # bottom time
    'vitesse_remontee_max': 8.5,   # max ascent (m/min)
    'houle': 'faible',             # sea state
    'visibilite_metres': 15,       # visibility
    'courant': 'aucun',            # current
    'dive_type': 'exploration',    # type
    'rating': 5,                   # rating (1-5)
    'notes': 'Magnifique plongée',
    'tags': ['Épave', 'Poissons']
}
```

---

## Database Tables Summary

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **dives** | Main dive records | id, date, site_id, profondeur_max, sac, rating |
| **sites** | Dive locations | id, nom, pays, coordonnees_gps |
| **buddies** | Dive partners | id, nom, niveau_certification |
| **tags** | Categories | id, nom, categorie |
| **dive_tags** | M2M relationship | dive_id, tag_id |
| **cached_dive_data** | Performance cache | dive_id, cached_dataframe, timestamp |

**Indexes**: date, site_id, rating, date+site composite

---

## Key Functions Cheat Sheet

### Database (database.py)
```python
# Query operations
get_all_dives()                    # All dives as DataFrame
get_dive_by_id(dive_id)           # Full dive details
get_all_sites_with_stats()        # Sites with aggregations
get_all_tags()                    # Unique tags list

# Mutations
insert_dive(dive_data)            # Save new dive
update_dive(dive_id, dive_data)   # Edit existing dive
delete_dive(dive_id)              # Remove dive (cascade)
update_site_coordinates(site_id)  # Update GPS coords

# Cache
save_dive_cache(dive_id, df)     # Store DataFrame
get_dive_cache(dive_id)          # Retrieve cached data
invalidate_dive_cache(dive_id)   # Clear cache
```

### Parser (parser.py)
```python
parse_dive_file(uploaded_file)   # Auto-detect & parse
# Supports: .fit, .xml, .uddf, .dl7
# Returns: DataFrame with standard columns
```

### Analyzer (analyzer.py)
```python
calculate_sac(df)                 # Air consumption
calculate_average_pressure(df)    # Weighted pressure
calculate_nitrogen_saturation(df) # Decompression model
detect_safety_stops(df)           # Identify paliers
```

### Visualizer (visualizer.py)
```python
create_dive_profile(df)           # Main profile graph
create_saturation_plot(df)        # N₂ saturation levels
calculate_ascent_speed(df)        # Speed calculations
```

### Validation (validation.py)
```python
validate_uploaded_file(file)      # Complete validation
validate_file_extension(filename) # Extension check
validate_file_size(file_size)     # Size check
validate_file_content(content)    # Magic bytes check
sanitize_filename(filename)       # Path traversal safety
```

---

## Configuration Quick Reference

```python
# Key values (config.py)
MAX_FILE_SIZE_MB = 50
MAX_DEPTH_M = 200.0
MAX_SAFE_ASCENT_SPEED_M_MIN = 10.0
WARNING_ASCENT_SPEED_M_MIN = 15.0
DEFAULT_TANK_VOLUME_L = 12.0
DB_PATH = ~/dive-analyzer/dive_log.db

# Allowed formats
ALLOWED_EXTENSIONS = {'.fit', '.xml', '.uddf', '.dl7'}

# Standard tags
['Épave', 'Grotte', 'Tombant', 'Nuit', 'Dérivante',
 'Formation', 'Technique', 'Faune', 'Flore', 'Photo', ...]
```

---

## File Format Support

| Format | Extension | Source | Parser |
|--------|-----------|--------|--------|
| FIT | .fit | Garmin, Suunto | FitParser (fitparse lib) |
| UDDF | .uddf, .xml | Subsurface, Universal | UddfParser (XML) |
| XML | .xml | Various computers | XmlParser |
| DL7 | .dl7 | OSTC (Heinrichs Weikamp) | DL7Parser |

---

## Common Workflows

### 1. Upload & Analyze Dive
```
User uploads file → Validation → Parsing → Physics calculations 
→ Visualization → Annotation form → Save to database
```

### 2. View Dive Statistics
```
Load all dives → Filter (site, date, depth, rating)
→ Display in table → Calculate aggregations
```

### 3. Edit Dive Metadata
```
Select dive → Show current values → Modify → Update DB
```

### 4. View Dive Sites Map
```
Get all sites with stats → Calculate map center
→ Create markers (color by dive count) → Add popups
```

---

## Performance Optimizations

### Database Indexes
- Fast date sorting: `idx_dives_date`
- Fast site lookups: `idx_dives_site_id`
- Fast rating filters: `idx_dives_rating`
- Combined queries: `idx_dives_date_site`

### Caching
- DataFrame pickle serialization in `cached_dive_data`
- Manual cache invalidation on updates
- Hit rate tracking via `get_cache_stats()`

### Design
- Lazy evaluation in Streamlit
- Foreign key constraints for data integrity
- Transaction rollback on errors

---

## Security Features

### Input Validation
- Magic byte verification (detect file renaming attacks)
- Filename sanitization (prevent path traversal)
- File size limits (50 MB max)
- Extension whitelist

### Data Protection
- Foreign key constraints (referential integrity)
- Cascade deletion (maintain consistency)
- Transaction rollback on errors
- Comprehensive logging

---

## Development Commands

### Running the App
```bash
streamlit run app.py              # Start web server
./start.sh                        # Via shell script
```

### Running Tests
```bash
pytest tests/                     # All tests
pytest tests/ -v                  # Verbose output
pytest tests/ --cov              # With coverage
pytest tests/test_database.py    # Single file
```

### Installing Dependencies
```bash
pip install -r requirements.txt  # Required packages
pip install pytest pytest-cov    # Testing tools
```

---

## Directory Locations

```
~/dive-analyzer/
├── dive_log.db              # SQLite database
├── dive_analyzer.log        # Application logs
├── uploads/                 # Stored dive files
├── backups/                 # Database backups
└── *.py                     # Source code
```

---

## Test Coverage by Module

| Module | Tests | Coverage |
|--------|-------|----------|
| validation.py | 41 tests | ~95% |
| parser.py | 55+ tests | ~85% |
| database.py | 60+ tests | ~90% |
| **Total** | **150+** | **>80%** |

---

## Common Issues & Solutions

### Issue: File upload rejected
**Solution**: Check magic bytes (validation.py), ensure .fit/.xml/.uddf/.dl7 extension

### Issue: Slow database queries
**Solution**: Use indexed queries (date, site_id), check cache statistics

### Issue: Dive not saved
**Solution**: Check database connection, validate required fields (site, date, metrics)

### Issue: Map not showing
**Solution**: Ensure sites have GPS coordinates in "lat,lon" format

---

## Next Features (Roadmap)

- PDF export of dives
- Advanced statistics (progression graphs)
- Auto GPS import from FIT files
- Bluetooth dive computer support
- Multi-user authentication
- Marine weather API
- Site clustering on map
- KML/GPX export

---

## Key Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Singleton | config.py | Single config instance |
| Strategy | parser.py | Multiple format parsers |
| Factory | database.py | Connection creation |
| MVC | pages/ | Page separation |
| DTO | Throughout | Data dictionaries |

---

## Contact & Resources

**Repository**: /home/user/dive-analyzer/
**Documentation**: See CODEBASE_OVERVIEW.md, CONTRIBUTING.md, README.md
**Tests**: tests/ directory (150+ test files)
**Logs**: dive_analyzer.log

---

**Last Updated**: 2025-11-07  
**Phase**: 2 Complete (Tests, Performance, Docs)  
**Status**: Production-ready with Phase 3 roadmap
