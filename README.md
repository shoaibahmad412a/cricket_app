# CureExchange Responses Sync Service

## Overview
A Windows Service that synchronizes medical claim responses and Electronic Remittance Advice (ERA) data from CureExchange server to multiple client practice databases. The service runs on configurable intervals and operates within specified time windows.

## Architecture

### Service Components
- **Service Host**: `ResponsesSyncService.cs` - Windows Service infrastructure
- **Orchestration Layer**: `ResponsesManager.cs` - Core business logic coordinator
- **Data Layer**: `ResponsesDataService.cs` & `ResponsesSQLHelper.cs` - Database operations
- **Service Installer**: `ResponsesSyncServiceInstaller.cs` - Windows Service installation configuration

## Core Functionalities

### 1. Service Initialization & Execution

#### Timer-Based Execution
The service operates on a configurable interval and time window:

```csharp
// ResponsesSyncService.cs - Lines 51-58
```
- Reads `TRIGGER_HOURS` and `END_HOURS` from configuration
- Initializes timer with `SERVICE_INTERVAL` (default: 10 seconds)
- Service only executes sync within allowed hours (e.g., 9 PM - 4 AM)

#### Time Window Validation
```csharp
// ResponsesSyncService.cs - Lines 127-137
```
Business Logic: Service checks if current time falls within configured hours before executing sync operations.

### 2. Multi-Practice Processing

#### Practice Discovery
```csharp
// ResponsesManager.cs - Lines 70-83
```
- Connects to `ControlDB` database
- Retrieves all client practices via `GetClientPractices()` stored procedure
- Each practice has its own database (SourceName)

#### Practice Iteration
```csharp
// ResponsesManager.cs - Lines 85-156
```
For each practice:
1. Extracts `dbName`, `practiceID`, and `practiceIdentifier`
2. Changes database context to practice-specific database
3. Retrieves practice credentials via `GetClientProfileSettings()` stored procedure
4. Sets authentication credentials for WCF service calls

### 3. Claims Response Status Synchronization

#### Core Business Logic
```csharp
// ResponsesManager.cs - Lines 158-291
```

**Process Flow:**
1. Calls `rsClient.GetClaimsResponseStatus()` to fetch claim responses from CureExchange server (Line 163)
2. Processes responses in batches until no more data available (Line 165)
3. Saves claim responses to database via `SaveClaimResponses()` (Line 169)

#### Response Type Handling
```csharp
// ResponsesDataService.cs - Lines 146-198
```
The service handles **two response types**:

**REC (Rejection/Acknowledgement) Responses:**
- Saves via `SaveRecResponse()` stored procedure (Line 148)
- Records detailed status with trace numbers and payer information
- Creates formatted response files with headers (Lines 54-56 in ResponseFile.cs)

**INS (Insurance) Responses:**
- Saves via `SaveInsResponse()` stored procedure (Line 173)
- Records claim status with payer references
- Generates different file format (Lines 58-60 in ResponseFile.cs)

#### Response Status Interpretation
```csharp
// ResponsesDataService.cs - Lines 125-144
```
Business Logic:
- **P/A Status**: Prefixed with "Acknowledgement:" or set to "Processed"
- **R Status**: Prefixed with "Rejected:"
- Empty responses default to "In Process" or "Rejected" based on status

#### Transaction Management
```csharp
// ResponsesManager.cs - Lines 186-203
```
- Commits transaction only if `UpdateSyncFlag()` succeeds when `ForceSyncFlagFalse=true`
- Rolls back on failure to maintain data integrity

### 4. ERA (Electronic Remittance Advice) Synchronization

#### Core Business Logic
```csharp
// ResponsesManager.cs - Lines 344-505
```

**Process Flow:**
1. Fetches ERA responses via `rsClient.GetERAResponses()` (Line 356)
2. Validates ERA mapping IDs to prevent duplicates (Line 369)
3. Processes each ERA response with X12 EDI document

#### ERA Validation Logic
```csharp
// ResponsesManager.cs - Lines 292-343
```
Extracts mapping IDs from nested ERA structure:
- **Transaction Level**: `TransactionEraMappingID` (Line 314)
- **Claim Level**: `EraMappingId` from each claim (Line 326)
- Returns dictionary with both mapping ID lists (Lines 339-340)

#### Duplicate Prevention
```csharp
// ResponsesManager.cs - Lines 375-392
```
Business Logic:
- Calls `IsSynced()` to check existing mapping IDs in database (Line 381)
- Only saves ERA responses with unsynced mapping IDs (Line 390)
- Ensures ERA data is not duplicated across sync cycles

#### ERA Transaction Processing
```csharp
// ResponsesDataService.cs - Lines 244-268
```
- Uses extended transactions for ERA data integrity
- Saves via `ERADataService.Save()` with X12 EDI document parsing (Line 256)
- Commits per-response to ensure partial success on failures (Line 397 in ResponsesManager.cs)

#### Post-Processing
```csharp
// ResponsesManager.cs - Lines 439-453
```
After each batch:
1. `UpdatePayerIDAndMarkAsProblematic()` - Updates payer information and flags issues (Line 442)
2. `UpdateIPrcIDAndMarkAsProblematic()` - Updates procedure codes and flags issues (Line 444)

#### Summary Generation
```csharp
// ResponsesManager.cs - Lines 469-483
```
- `UpdateERASyncComplete()` - Marks ERA records as fully synced (Line 472)
- `InsertERASummaryReport()` - Generates summary report for monitoring (Line 473)

### 5. Authentication & Error Handling

#### WCF Service Connection
```csharp
// ResponsesManager.cs - Lines 52-67
```
- Establishes connection to CureExchange ResponseService
- Validates connection state before proceeding
- Throws exception if connection fails

#### Authentication Failure Handling
```csharp
// ResponsesManager.cs - Lines 136-139, 251-258, 488-493
```
Business Logic:
- Catches `AuthenticationFailedFault` exceptions
- If practice is inactive (`IsPracticeActive == false`), disables sync service for that practice
- Prevents repeated failed authentication attempts

#### Practice Service Deactivation
```csharp
// ResponsesDataService.cs - Lines 283-301
```
Calls `DisableCXService()` stored procedure to set `ResponsesSync=false` for the practice.

### 6. Database Operations

#### Dynamic Database Switching
```csharp
// BaseSQLHelper.cs - Lines 30-51
```
Business Logic: Service dynamically switches between ControlDB and practice-specific databases using environment variable for server name.

#### Transaction Management
```csharp
// BaseSQLHelper.cs - Lines 141-173
```
- **Commit**: Finalizes all changes when operations succeed (Lines 141-156)
- **Rollback**: Reverts all changes on failure (Lines 158-173)
- Separate transaction handling for Claims vs ERA operations

## Configuration

### App Settings (`app.config`)

| Setting | Description | Default |
|---------|-------------|---------|
| `TRIGGER_HOURS` | Service start hour (24-hour format) | 21 (9 PM) |
| `END_HOURS` | Service stop hour (24-hour format) | 04 (4 AM) |
| `SERVICE_INTERVAL` | Timer interval in milliseconds | 10000 (10 sec) |
| `SecurityProtocols` | SSL/TLS protocols (192=SSL3, 768=TLS1, 3072=TLS1.2) | 192\|768\|3072 |
| `ForceSyncFlagFalse` | Require sync flag update before commit | True |
| `UserInteractive` | Run as console app instead of service | True |
| `EDIQueriesTimeout` | Database query timeout in seconds | 300 |

### WCF Endpoint Configuration
```xml
<!-- app.config - Line 80 -->
<endpoint address="https://ccservices.curemd.net/wcf/responses/ResponseService.svc" 
          binding="wsHttpBinding" 
          contract="ResponsesService.IResponseService" />
```

### Logging Configuration
```csharp
// ResponsesSyncService.cs - Lines 20-37
```
- **Target**: Elasticsearch at `curemd-domain-apis.es.us-east-1.aws.found.io`
- **Index**: `services.era.sync`
- **Server Tag**: Retrieved from machine environment variable `db_server_name`

## Database Stored Procedures

### Control Database (ControlDB)
- `GetExchangeServerPracticesInfo` - Retrieves all active practices
- `stp_EDI_DisableEDIService` - Disables sync service for a practice

### Practice Databases
**Configuration:**
- `GetPracticeProfileSettings` - Gets practice credentials and settings

**Claims Response:**
- `stp_CX_GetResponse_Type` - Determines if response is REC or INS
- `stp_CX_InsertREC_Response` - Saves REC response data
- `stp_CX_InsertINS_Response` - Saves INS response data
- `stp_CX_InsertRec_Response_Status` - Saves REC response status details
- `stp_CX_InsertINS_Response_Status` - Saves INS response status details
- `stp_CX_Insert_Response_Interpretation` - Saves response interpretation
- `stp_CX_UpdateClaimStatus_DetailLog` - Updates claim status in detail log
- `stp_EDI_Claim_GetClaimFileInfo` - Retrieves claim file information
- `InsertRECINSFileData` - Saves formatted response file data

**ERA Processing:**
- `stp_ERA_GetUnSyncedMappingIds` - Checks for duplicate ERA mapping IDs
- `stp_ERA_UpdatePayerIDAndMarkAsProblematic` - Updates payer data and flags issues
- `stp_ERA_UpdateIPrcIDAndMarkAsProblematic` - Updates procedure data and flags issues
- `stp_ERA_UpdateSyncComplete` - Marks ERA records as synced
- `stp_EDI_InsertERASummaryReport` - Generates ERA summary reports

## Installation

### Service Installation
```csharp
// ResponsesSyncServiceInstaller.cs - Lines 17-33
```
- **Service Name**: `CXResponsesSyncService`
- **Display Name**: CureExchange Responses Sync Service
- **Account**: LocalSystem
- **Start Type**: Automatic (Delayed)

### Installation Commands
```powershell
# Install service
installutil.exe CureExchange.Client.Responses.SyncService.exe

# Uninstall service
installutil.exe /u CureExchange.Client.Responses.SyncService.exe
```

### User Interactive Mode
```csharp
// Program.cs - Lines 27-50
```
For debugging, set `UserInteractive=True` in app.config to run as console application.

## Key Design Patterns

### 1. Template Method Pattern
`BaseDataService` and `BaseSQLHelper` provide abstract base classes with common database operations.

### 2. Factory Pattern
`ResponseFilesManager` creates and manages `ResponseFile` instances based on file type (REC/INS).

### 3. Transaction Script Pattern
Each sync operation follows a scripted transaction flow with explicit commit/rollback.

### 4. Service Layer Pattern
`ResponsesManager` orchestrates all business logic, keeping controllers thin.

## Error Handling Strategy

1. **Service Level**: Logs errors to Elasticsearch but continues processing other practices
2. **Practice Level**: Disables problematic practices to prevent repeated failures
3. **Transaction Level**: Rolls back database changes on any error
4. **Batch Level**: Processes claims/ERAs individually to maximize successful records

## Dependencies

- **.NET Framework**: 4.8
- **Serilog**: Logging framework with Elasticsearch sink
- **WCF**: Communication with CureExchange server
- **SQL Server**: Data persistence
- **ANSIASCX12.EDI**: X12 EDI document parsing for ERA

## Environment Requirements

- **Machine Environment Variable**: `db_server_name` - SQL Server instance name
- **Network Access**: HTTPS connection to `ccservices.curemd.net`
- **Database Access**: SQL Server login (`curemd` / `cure2000`)
- **Elasticsearch Access**: For centralized logging

---

**Version**: 1.0  
**Framework**: .NET Framework 4.8  
**Service Type**: Windows Service (Automatic Start - Delayed)  
**License**: Proprietary - CureExchange Client Application
