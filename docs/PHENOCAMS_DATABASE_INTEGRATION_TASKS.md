# PhenoTag-to-Phenocams Database Integration - Implementation Tasks

## Overview

This document outlines the tasks required to implement direct database integration between PhenoTag annotations and the Phenocams v2 processing pipeline. Currently, PhenoTag saves annotations to YAML files, but these annotations are not automatically transferred to the Phenocams DuckDB database.

**Goal**: Enable PhenoTag to write manual quality flags and discard decisions directly to the Phenocams station databases, allowing L2/L3 processing to use human expert observations.

## Architecture Decision

**Chosen Approach**: PhenoTag writes directly to Phenocams DuckDB database

**Rationale**:
- Both systems operate on the same filesystem
- PhenoTag already discovers L1 images from Phenocams directories
- Direct database write is simpler than intermediate import scripts
- Real-time updates - no separate import step needed
- Maintains data integrity through DuckDB ACID properties

## Prerequisites

- [ ] Review Phenocams database schema (`phenocams/src/phenocams/database.py`)
- [ ] Understand current annotation file structure (`docs/configuration/annotation_files_schema.md`)
- [ ] Map PhenoTag annotation fields to Phenocams database columns
- [ ] Decide on conflict resolution strategy (manual overrides automatic)

## Implementation Tasks

### Phase 1: Database Connection Module

#### Task 1.1: Create DuckDB Connection Handler

**File**: `src/phenotag/database/phenocams_db.py` (new module)

**Requirements**:
- [ ] Create `PhenocamsDatabase` class
- [ ] Implement connection to station DuckDB files
- [ ] Handle database path resolution: `{data_dir}/{station}/phenocams/database/{station}.duckdb`
- [ ] Implement connection pooling/context manager
- [ ] Add error handling for missing database files
- [ ] Add read-only mode for safety (default)
- [ ] Add read-write mode with explicit enable flag

**Code Structure**:
```python
class PhenocamsDatabase:
    """Interface to Phenocams station DuckDB database."""

    def __init__(self, station: str, data_dir: str, read_only: bool = True):
        """Initialize database connection."""

    def get_l1_image_by_filename(self, filename: str) -> Optional[Dict]:
        """Query L1 image record by filename."""

    def update_image_flags(self, image_id: int, flags: Dict,
                          discarded: bool, discard_reason: str) -> bool:
        """Update flags and discard status for an image."""

    def update_roi_stats_discard(self, image_id: int, roi_name: str,
                                 discarded: bool, reason: str) -> bool:
        """Update discard status for specific ROI."""
```

**Testing**:
- [ ] Unit tests for connection handling
- [ ] Test with actual Phenocams database
- [ ] Test error handling for missing/corrupted databases
- [ ] Test read-only vs read-write modes

---

#### Task 1.2: Add Database Configuration

**File**: `src/phenotag/config/database_config.py` (new file)

**Requirements**:
- [ ] Define database paths configuration
- [ ] Define flag prefix conventions (`manual_` prefix)
- [ ] Define conflict resolution strategy
- [ ] Add database connection timeout settings
- [ ] Add transaction batch size settings

**Configuration Format**:
```python
DATABASE_CONFIG = {
    'flag_prefix': 'manual_',  # Prefix for PhenoTag flags
    'conflict_resolution': 'manual_overrides',  # or 'flag_counting'
    'connection_timeout': 30,  # seconds
    'batch_size': 100,  # images per transaction
    'read_only_default': True,  # Safety first
}
```

---

### Phase 2: Annotation-to-Database Mapper

#### Task 2.1: Implement Flag Mapping Logic

**File**: `src/phenotag/database/annotation_mapper.py` (new module)

**Requirements**:
- [ ] Map PhenoTag annotation structure to database fields
- [ ] Merge automatic flags with manual flags
- [ ] Apply `manual_` prefix to all PhenoTag flags
- [ ] Handle snow_presence → `manual_snow` flag
- [ ] Handle custom user flags with proper prefixing
- [ ] Implement conflict resolution (manual overrides automatic)

**Code Structure**:
```python
class AnnotationMapper:
    """Maps PhenoTag annotations to Phenocams database format."""

    def map_roi_annotations_to_flags(self, roi_annotations: List[Dict]) -> Dict:
        """Convert ROI annotations to merged flags dict."""

    def resolve_discard_conflict(self, auto_discard: bool,
                                 manual_discard: bool) -> Tuple[bool, str]:
        """Resolve conflict between automatic and manual discard."""

    def merge_flags(self, auto_flags: Dict, manual_flags: Dict,
                   overwrite: bool = False) -> Dict:
        """Merge automatic and manual flags."""
```

**Flag Mapping Examples**:
```python
# PhenoTag annotation
{
    "roi_name": "ROI_00",
    "discard": true,
    "snow_presence": true,
    "flags": ["fog", "frost"]
}

# Maps to Phenocams flags
{
    "low_brightness": true,         # Existing automatic flag
    "high_solar_zenith": false,     # Existing automatic flag
    "manual_fog": true,             # From PhenoTag
    "manual_frost": true,           # From PhenoTag
    "manual_snow": true,            # From snow_presence
    "manual_discard": true          # From discard field
}
```

**Testing**:
- [ ] Unit tests for flag mapping
- [ ] Test conflict resolution scenarios
- [ ] Test flag merging with various combinations
- [ ] Test edge cases (empty flags, null values)

---

#### Task 2.2: Implement ROI-Level Discard Tracking

**File**: Same as Task 2.1

**Requirements**:
- [ ] Map per-ROI discard flags to `roi_stats` table
- [ ] Generate discard reason from ROI flags
- [ ] Handle case where some ROIs discarded, others not
- [ ] Determine image-level discard from ROI-level discards

**Logic**:
```python
def determine_image_discard(roi_annotations: List[Dict]) -> Tuple[bool, str]:
    """
    Determine if entire image should be discarded based on ROI annotations.

    Rule: If ANY ROI is marked as discarded, the image is discarded.

    Returns:
        (discarded, reason)
    """
    discarded_rois = [roi for roi in roi_annotations if roi.get('discard', False)]

    if discarded_rois:
        reasons = []
        for roi in discarded_rois:
            flags = roi.get('flags', [])
            if flags:
                reasons.append(f"{roi['roi_name']}: {', '.join(flags)}")

        return True, f"Manual review - {'; '.join(reasons)}"

    return False, None
```

---

### Phase 3: UI Integration

#### Task 3.1: Add Database Write Toggle to UI

**File**: `src/phenotag/ui/components/sidebar.py`

**Requirements**:
- [ ] Add "Enable Database Updates" toggle to Configuration panel
- [ ] Default to OFF for safety
- [ ] Show warning when enabled
- [ ] Display database connection status
- [ ] Show last database write timestamp
- [ ] Add "Test Database Connection" button

**UI Components**:
```python
# In sidebar configuration section
st.checkbox(
    "Enable Database Updates",
    value=False,
    help="⚠️ Enable writing annotations directly to Phenocams database. "
         "This will update flags and discard status for L1 images."
)

if st.session_state.get('database_updates_enabled'):
    st.warning("⚠️ Database updates are ENABLED. Annotations will be written to Phenocams database.")

    # Connection status
    if test_database_connection():
        st.success(f"✓ Connected to database: {station}.duckdb")
    else:
        st.error("✗ Database connection failed")
```

---

#### Task 3.2: Integrate Database Writes into Save Workflow

**File**: `src/phenotag/ui/components/annotation.py`

**Requirements**:
- [ ] Modify `save_all_annotations()` to optionally write to database
- [ ] Write to YAML first (preserve existing behavior)
- [ ] Then write to database if enabled
- [ ] Show progress during database writes
- [ ] Handle database write errors gracefully
- [ ] Log database write results
- [ ] Add rollback capability if database write fails

**Modified Save Flow**:
```python
def save_all_annotations(force_save=False, write_to_database=False):
    """
    Save annotations to YAML and optionally to Phenocams database.

    Args:
        force_save: Save even if no changes detected
        write_to_database: Write annotations to Phenocams database
    """
    try:
        # Step 1: Save to YAML (existing behavior)
        yaml_success = save_annotations_to_yaml(...)

        if not yaml_success:
            st.error("Failed to save annotations to YAML")
            return False

        # Step 2: Optionally write to database
        if write_to_database and st.session_state.get('database_updates_enabled'):
            with st.spinner("Writing annotations to database..."):
                db_result = write_annotations_to_database(...)

                if db_result['success']:
                    st.success(f"✓ Updated {db_result['updated_count']} images in database")
                else:
                    st.warning(f"⚠️ Database write partially failed: {db_result['errors']}")

        return True

    except Exception as e:
        st.error(f"Error saving annotations: {e}")
        return False
```

---

#### Task 3.3: Add Database Write Summary Panel

**File**: `src/phenotag/ui/components/database_summary.py` (new module)

**Requirements**:
- [ ] Show database write statistics
- [ ] Display images updated count
- [ ] Show manual override count
- [ ] List flags added by category
- [ ] Show any errors/warnings
- [ ] Add "View Database Log" expander

**UI Design**:
```
📊 Database Write Summary
├─ Images Updated: 23
├─ Manual Overrides: 5 (automatic discard → manual keep)
├─ Flags Added:
│  ├─ manual_fog: 8 images
│  ├─ manual_snow: 12 images
│  └─ manual_obstruction: 3 images
└─ Errors: 0
```

---

### Phase 4: Safety and Validation

#### Task 4.1: Implement Database Backup

**File**: `src/phenotag/database/backup.py` (new module)

**Requirements**:
- [ ] Create database backup before first write
- [ ] Store backup with timestamp
- [ ] Implement backup rotation (keep last 5)
- [ ] Add manual backup trigger button
- [ ] Add restore from backup functionality

**Backup Location**:
```
{data_dir}/{station}/phenocams/database/backups/
├── {station}_backup_20251007_143022.duckdb
├── {station}_backup_20251007_150133.duckdb
└── ...
```

---

#### Task 4.2: Add Validation and Dry-Run Mode

**File**: `src/phenotag/database/validator.py` (new module)

**Requirements**:
- [ ] Validate annotations before database write
- [ ] Check that L1 images exist in database
- [ ] Verify ROI names match configured ROIs
- [ ] Implement dry-run mode (simulate without writing)
- [ ] Generate validation report
- [ ] Show preview of changes before applying

**Validation Checks**:
```python
def validate_annotations_for_database(annotations: Dict,
                                     database: PhenocamsDatabase) -> Dict:
    """
    Validate annotations before database write.

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str],
            'preview': {
                'images_to_update': int,
                'flags_to_add': Dict[str, int],
                'overrides': List[str]
            }
        }
    """
```

---

#### Task 4.3: Implement Transaction Logging

**File**: `src/phenotag/database/transaction_log.py` (new module)

**Requirements**:
- [ ] Log all database writes to JSON file
- [ ] Record timestamp, user, images affected
- [ ] Record old vs new values for audit trail
- [ ] Add transaction ID for rollback capability
- [ ] Create log viewer in UI

**Log Entry Format**:
```json
{
  "transaction_id": "txn_20251007_143022",
  "timestamp": "2025-10-07T14:30:22Z",
  "station": "Svartberget",
  "instrument": "ANS-SvB-P01",
  "day_of_year": "001",
  "year": "2024",
  "images_updated": 23,
  "changes": [
    {
      "filename": "Svartberget_ANS-SvB-P01_2024_001_20240101_090000.jpg",
      "image_id": 12345,
      "old_values": {
        "discarded": false,
        "flags": {"low_brightness": true}
      },
      "new_values": {
        "discarded": true,
        "discard_reason": "Manual review: ROI_00: fog, frost",
        "flags": {
          "low_brightness": true,
          "manual_fog": true,
          "manual_frost": true,
          "manual_snow": true
        }
      }
    }
  ]
}
```

---

### Phase 5: Testing and Documentation

#### Task 5.1: Create Integration Tests

**File**: `tests/test_phenocams_integration.py` (new file)

**Requirements**:
- [ ] Test full annotation-to-database flow
- [ ] Test with sample Phenocams database
- [ ] Test conflict resolution scenarios
- [ ] Test error handling and rollback
- [ ] Test with multiple stations/instruments
- [ ] Performance test with large annotation files

**Test Scenarios**:
1. Happy path: annotations write successfully
2. Conflict resolution: manual overrides automatic
3. Missing image: annotation skipped with warning
4. Database locked: retry logic
5. Partial failure: rollback transaction
6. ROI-level discard propagation

---

#### Task 5.2: Update User Documentation

**Files to Update**:
- [ ] `README.md` - Add database integration overview
- [ ] `docs/user-guide/database_integration.md` (new) - Comprehensive guide
- [ ] `docs/configuration/database_config.md` (new) - Configuration reference
- [ ] `docs/api-reference/annotation_system.md` - Update with database writes

**Documentation Sections**:
1. Overview of database integration
2. Enabling database updates (safety warning)
3. What data is written to database
4. How to verify database updates
5. Troubleshooting database connection issues
6. Rollback procedure if needed

---

#### Task 5.3: Create Developer Guide

**File**: `docs/developer-guide/phenocams_database_integration.md` (new)

**Requirements**:
- [ ] Document database schema mapping
- [ ] Explain flag naming conventions
- [ ] Document conflict resolution logic
- [ ] Provide code examples
- [ ] Explain transaction logging
- [ ] Document backup/restore procedures

---

### Phase 6: Deployment and Validation

#### Task 6.1: Create Migration Script

**File**: `scripts/migrate_yaml_to_database.py` (new)

**Purpose**: One-time import of existing YAML annotations to database

**Requirements**:
- [ ] Scan for all existing annotation YAML files
- [ ] Import annotations to databases
- [ ] Generate migration report
- [ ] Handle errors gracefully
- [ ] Support dry-run mode
- [ ] Create backup before migration

**Usage**:
```bash
# Dry-run to see what would be imported
python scripts/migrate_yaml_to_database.py --dry-run

# Import all annotations for a station
python scripts/migrate_yaml_to_database.py --station Svartberget

# Import specific year
python scripts/migrate_yaml_to_database.py --station Svartberget --year 2024
```

---

#### Task 6.2: Create Validation Report Tool

**File**: `scripts/validate_database_annotations.py` (new)

**Purpose**: Verify database annotations match YAML files

**Requirements**:
- [ ] Compare YAML annotations with database records
- [ ] Report discrepancies
- [ ] Check for orphaned database flags
- [ ] Verify ROI-level discard consistency
- [ ] Generate validation report

---

#### Task 6.3: Performance Optimization

**Requirements**:
- [ ] Batch database writes (100 images per transaction)
- [ ] Use prepared statements for updates
- [ ] Implement connection pooling
- [ ] Add progress indicators for large datasets
- [ ] Profile database write performance
- [ ] Optimize query patterns

---

## Implementation Priority

### Priority 1 (Critical Path)
1. Task 1.1: Database connection handler
2. Task 1.2: Database configuration
3. Task 2.1: Flag mapping logic
4. Task 3.2: Integrate database writes into save workflow

**Deliverable**: Basic working database integration

### Priority 2 (Safety & UI)
5. Task 3.1: Database write toggle UI
6. Task 4.1: Database backup
7. Task 4.2: Validation and dry-run

**Deliverable**: Safe, user-friendly integration

### Priority 3 (Polish & Documentation)
8. Task 2.2: ROI-level discard tracking
9. Task 3.3: Database write summary panel
10. Task 4.3: Transaction logging
11. Task 5.2: User documentation

**Deliverable**: Production-ready feature with full documentation

### Priority 4 (Operations & Migration)
12. Task 5.1: Integration tests
13. Task 6.1: Migration script for existing annotations
14. Task 6.2: Validation report tool
15. Task 6.3: Performance optimization

**Deliverable**: Tools for deployment and validation

## Success Criteria

- [ ] Annotations saved in PhenoTag automatically update Phenocams database
- [ ] Manual flags properly prefixed with `manual_`
- [ ] Conflict resolution works correctly (manual overrides automatic)
- [ ] Database writes are atomic (all or nothing)
- [ ] Backup created before first write
- [ ] UI clearly indicates when database updates are enabled
- [ ] Performance acceptable (< 1 second for 100 images)
- [ ] Comprehensive error handling and logging
- [ ] All tests pass
- [ ] Documentation complete

## Estimated Effort

| Phase | Tasks | Estimated Hours |
|-------|-------|-----------------|
| Phase 1: Database Connection | 2 tasks | 8 hours |
| Phase 2: Annotation Mapping | 2 tasks | 12 hours |
| Phase 3: UI Integration | 3 tasks | 16 hours |
| Phase 4: Safety Features | 3 tasks | 12 hours |
| Phase 5: Testing & Docs | 3 tasks | 16 hours |
| Phase 6: Deployment | 3 tasks | 8 hours |
| **Total** | **16 tasks** | **72 hours** |

## Dependencies

- Phenocams v3.10.1+ (current database schema)
- DuckDB Python library (already available)
- No changes required to Phenocams codebase
- PhenoTag can operate independently if database unavailable

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database corruption | HIGH | Automatic backup before writes, read-only default mode |
| Performance issues with large datasets | MEDIUM | Batch writes, connection pooling, progress indicators |
| Conflicting writes from multiple users | LOW | DuckDB handles concurrency, transaction logging for audit |
| Missing L1 images in database | LOW | Validation step, skip with warning, log missing images |

## Future Enhancements

- [ ] Real-time sync mode (auto-save triggers database write)
- [ ] Undo functionality (rollback last transaction)
- [ ] Batch annotation import from external sources
- [ ] Database annotation viewer (show all manual flags)
- [ ] Statistics dashboard (manual vs automatic discard rates)
- [ ] API endpoint for programmatic annotation updates

---

**Document Version**: 1.0
**Created**: 2025-10-07
**Status**: Ready for Implementation
**Estimated Completion**: 2-3 weeks (1 developer)
