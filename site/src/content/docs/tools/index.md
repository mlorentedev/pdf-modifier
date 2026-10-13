---
title: MCP Tools Reference
description: Detailed reference for all pdf-modifier MCP tools with parameters, examples, and error codes.
---

## read_pdf_structure

Extract the complete structural content of a PDF document.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | `string` | Yes | Absolute path to the PDF file |
| `password` | `string` | No | Password if the PDF is encrypted |

### Response

Returns JSON with the full page hierarchy:

```json
{
  "success": true,
  "file_path": "/path/to/document.pdf",
  "total_pages": 2,
  "pages": [
    {
      "page": 1,
      "width": 612.0,
      "height": 792.0,
      "elements": [
        {
          "text": "Invoice #12345",
          "bbox": [72.0, 72.0, 200.0, 84.0],
          "origin": [72.0, 82.5],
          "font": "Helvetica-Bold",
          "size": 12.0,
          "color": 0
        }
      ]
    }
  ]
}
```

### Usage tip

Call this tool first to understand the document layout. The `bbox` and `origin` values help identify exact text positions, and `font`/`size` show what styling will be preserved during replacement.

---

## inspect_pdf_fonts

Search for specific text terms and report their font properties.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | `string` | Yes | Absolute path to the PDF file |
| `terms` | `string[]` | Yes | List of text strings to search (1-50 terms) |
| `password` | `string` | No | Password if the PDF is encrypted |

### Response

```json
{
  "success": true,
  "file_path": "/path/to/document.pdf",
  "terms_searched": ["Invoice", "Total"],
  "matches": [
    {
      "page": 1,
      "term": "Invoice",
      "context": "Invoice #12345 - January 15, 2025",
      "font": "Helvetica-Bold",
      "size": 12.0,
      "origin": [72.0, 82.5]
    }
  ],
  "total_matches": 1
}
```

### Usage tip

Run this before `modify_pdf_content` to verify that target text exists and understand its font properties. The `context` field shows surrounding text to help disambiguate partial matches.

---

## modify_pdf_content

Find and replace text in a PDF while preserving font styles.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | `string` | Yes | Absolute path to the source PDF |
| `output_path` | `string` | Yes | Absolute path for the modified PDF |
| `replacements` | `object` | Yes | Dictionary mapping old text to new text |
| `use_regex` | `boolean` | No | Treat keys as regex patterns (default: `false`) |
| `password` | `string` | No | Password if the PDF is encrypted |

### Response

```json
{
  "success": true,
  "input_path": "/path/to/input.pdf",
  "output_path": "/path/to/output.pdf",
  "replacements_made": 3,
  "pages_modified": 2,
  "warnings": []
}
```

### Replacement syntax

**Simple text replacement:**
```json
{"$99.99": "$149.99", "Draft": "Final"}
```

**Regex patterns** (with `use_regex: true`):
```json
{"Order #\\d+": "Order #REDACTED", "\\d{2}/\\d{2}/\\d{4}": "01/01/2025"}
```

**Hyperlink creation** (append `|URL`):
```json
{"Click Here": "Visit Site|https://example.com"}
```

**Link neutralization** (append `|void(0)`):
```json
{"Product Name": "Product Name|void(0)"}
```

### Important behaviors

- Text is matched within individual spans first, then a second pass matches across span boundaries within the same line
- Font style is approximated using Base 14 fonts (Helvetica, Times, Courier)
- Replacement text should be similar length to avoid visual overlap
- Maximum 100 replacements per call

---

## list_pdf_hyperlinks

Extract all existing hyperlinks and clickable URIs from a PDF.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | `string` | Yes | Absolute path to the PDF file |
| `password` | `string` | No | Password if the PDF is encrypted |

### Response

```json
{
  "success": true,
  "file_path": "/path/to/document.pdf",
  "total_links": 2,
  "links": [
    {
      "page": 1,
      "uri": "https://example.com",
      "bbox": [72.0, 100.0, 200.0, 112.0],
      "text": "Visit our website"
    }
  ]
}
```

---

## batch_modify_pdf_content

Apply the same text replacements to multiple PDF files at once. Each file is processed independently — a failure in one file does not stop the rest.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_paths` | `string[]` | Yes | List of absolute paths to input PDF files |
| `output_dir` | `string` | Yes | Directory where modified PDFs will be saved |
| `replacements` | `object` | Yes | Dictionary mapping old text to new text |
| `use_regex` | `boolean` | No | Treat keys as regex patterns (default: `false`) |
| `password` | `string` | No | Password if PDFs are encrypted |

### Response

```json
{
  "total_files": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "success": true,
      "input_path": "/path/to/a.pdf",
      "output_path": "/path/to/output/a.pdf",
      "replacements_made": 5,
      "pages_modified": 2,
      "warnings": []
    }
  ],
  "errors": [
    {"file": "/path/to/missing.pdf", "error": "PDF file not found: ..."}
  ]
}
```

### Usage tip

Use this for bulk operations like redacting dates across a folder of invoices. Output files are written to `output_dir` using the same filename as the input.

---

## Error codes

All tools return structured JSON errors with typed codes:

| Code | Description |
|------|-------------|
| `FILE_NOT_FOUND` | PDF file does not exist or is not accessible |
| `FILE_TOO_LARGE` | PDF exceeds the maximum allowed size (default 100 MB) |
| `READ_ERROR` | Failed to read or parse PDF (may be corrupted) |
| `WRITE_ERROR` | Failed to write output PDF |
| `PASSWORD_ERROR` | PDF requires a password but none (or incorrect) was provided |
| `INVALID_PATTERN` | Regex pattern is invalid |
| `UNEXPECTED_ERROR` | Unhandled error (check logs) |

Error response format:

```json
{
  "success": false,
  "error": "PASSWORD_ERROR",
  "message": "PDF is password protected. Please provide a password.",
  "details": {}
}
```
