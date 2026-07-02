#!/usr/bin/env python
"""Quick import test"""

try:
    from app.core.exceptions import ApplicationError
    print("✓ Core exceptions OK")
    
    from app.core.logger import get_logger
    print("✓ Core logger OK")
    
    from app.domain import ExportRequest, BackupRequest, ScheduleRequest
    print("✓ Domain models OK")
    
    from app.repositories import MongoDBRepository
    print("✓ Repositories OK")
    
    from app.processor import CSVProcessor
    print("✓ Processor OK")
    
    from app.services.connection_service import ConnectionService
    print("✓ Connection service OK")
    
    from app.services.export_service import ExportService
    print("✓ Export service OK")
    
    from app.services.backup_service import BackupService
    print("✓ Backup service OK")
    
    from app.routes.api import router
    print("✓ Routes OK")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
