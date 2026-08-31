# SharePoint Metadata in Fabric and Purview

## Recommended flow

```text
SharePoint Online
  -> Microsoft Fabric Data Factory pipeline or Dataflow Gen2
  -> Fabric Lakehouse / Warehouse landing table
  -> curated table with canonical metadata columns
  -> Microsoft Purview scan of the Fabric workspace
```

Purview is the catalog and governance layer. Fabric is the ingestion and storage layer. Do not treat a SharePoint custom column as a Purview asset by itself; land the value in a Fabric table or file, then scan that Fabric item.

## Canonical metadata model

Create a curated table such as `curated.sharepoint_documents` with one row per SharePoint file and these columns:

| Canonical column | SharePoint source | Notes |
| --- | --- | --- |
| `source_system` | constant `SharePoint` | Identifies the origin |
| `site_id` | Graph site id | Stable site identifier |
| `site_url` | site web URL | Human-readable source |
| `drive_id` | document library drive id | Stable library identifier |
| `item_id` | Graph drive item id | Stable file identifier |
| `file_name` | `name` | Original file name |
| `file_url` | `webUrl` | Link back to SharePoint |
| `library_name` | document library title | Source library |
| `folder_path` | parent path | Folder hierarchy |
| `content_type` | SharePoint content type name | For example, `Document` |
| `author` | `createdBy.user.email` | Creator |
| `editor` | `lastModifiedBy.user.email` | Last editor |
| `created_at` | `createdDateTime` | Store as UTC timestamp |
| `modified_at` | `lastModifiedDateTime` | Store as UTC timestamp |
| `file_size_bytes` | `size` | File size |
| `version` | SharePoint version label | Preserve as string |
| `sensitivity_label` | Purview/SharePoint label, when available | Do not infer this value |
| `business_owner` | custom column `BusinessOwner` | Normalize to email or UPN |
| `department` | custom column `Department` | Controlled vocabulary recommended |
| `document_status` | custom column `DocumentStatus` | Controlled vocabulary recommended |
| `retention_label` | custom column `RetentionLabel` | Preserve the source label |

Use the Graph IDs and timestamps as the technical keys. Custom columns should be copied into explicit, typed columns rather than kept only inside a JSON blob.

## Fabric implementation

1. In Fabric Data Factory, create a SharePoint Online or Microsoft Graph connection using an Entra ID service principal or managed identity. Grant only the required site permissions, preferably `Sites.Selected`.
2. Copy the SharePoint file inventory and its list/library fields into a Lakehouse landing table, for example `raw.sharepoint_items`.
3. Add a transformation to rename fields, convert timestamps to UTC, flatten person/choice fields, and validate controlled values.
4. Write the result to `curated.sharepoint_documents`. Keep the original `item_id`, `drive_id`, and `file_url` so that lineage and reprocessing are possible.
5. For document content, store the file in a Lakehouse Files area or OneLake shortcut and keep its path in `content_path`. Keep metadata in the curated table even when the binary is stored elsewhere.

Example SQL for a Warehouse or SQL endpoint transformation:

```sql
CREATE TABLE curated.sharepoint_documents AS
SELECT
    'SharePoint' AS source_system,
    site_id,
    site_url,
    drive_id,
    item_id,
    file_name,
    file_url,
    library_name,
    folder_path,
    content_type,
    created_by_email AS author,
    modified_by_email AS editor,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CAST(modified_at AS TIMESTAMP) AS modified_at,
    file_size_bytes,
    version,
    sensitivity_label,
    business_owner,
    department,
    document_status,
    retention_label
FROM raw.sharepoint_items
WHERE is_deleted = FALSE;
```

Adjust the SQL types and syntax to the selected Fabric engine. The important contract is the canonical column set, not the exact DDL.

## Purview catalog configuration

1. Register or select the Microsoft Fabric source in the Purview portal for the same tenant.
2. Configure a scan for the Fabric workspace and select the Lakehouse or Warehouse that contains `curated.sharepoint_documents`.
3. Enable schema extraction and lineage. Run the scan after the pipeline has created or changed the curated item.
4. In Purview, classify or label the canonical columns that contain personal, confidential, retention, or business-domain information.
5. Add glossary terms such as `Business Owner`, `Document Status`, and `Retention Label` and associate them with the curated columns.
6. Validate that the Purview asset is the Fabric table and that its description contains the SharePoint `file_url` and source identifiers. Purview will catalog the Fabric asset; it is not a replacement for SharePoint field mapping.

## Connecting this API

The current API uploads PDFs to Azure Blob Storage and relies on an Azure AI Search indexer. It does not currently connect to Fabric or Purview. If the API remains part of the ingestion path, add the canonical metadata to its document record and pass these values to the search index as filterable fields:

```text
source_system, site_id, drive_id, item_id, file_url,
library_name, folder_path, author, modified_at,
business_owner, department, document_status
```

The Fabric pipeline should remain the system of record for catalog metadata. The API should consume the curated metadata or receive it alongside a document upload, then use `item_id` as the idempotency key. Do not call Purview synchronously for every PDF upload; catalog scans and lineage updates are batch-oriented platform operations.

## Validation checklist

- A SharePoint file with a populated custom column appears in `raw.sharepoint_items`.
- The same value appears in the typed column in `curated.sharepoint_documents`.
- The curated table is visible as a Fabric asset in Purview after the scan.
- The column has the expected classification or glossary association.
- Updating the SharePoint file changes `modified_at` and updates the curated row without creating a duplicate `item_id`.
- Deleting a SharePoint file marks or removes the curated row according to the retention policy.
- `file_url` resolves for a user with the appropriate SharePoint permission.