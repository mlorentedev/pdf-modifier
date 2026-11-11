---
id: "VIS-001"
type: spec
status: active
created: "2026-06-19"
feature: Vision and OCR Capabilities
---

# VIS-001: Vision and OCR Capabilities

## What

Add vision-based capabilities using mimo-v2.6-flash (the router's vision default) to: OCR scanned PDFs without text layers, detect signatures and seals, compare PDFs visually, and analyze visual elements.

## Why

- Many PDFs are scanned images without text layers
- fitz can't extract text from image-only PDFs
- Signature/seal detection is needed for compliance
- Visual comparison catches differences text-based tools miss

## Scope

### In Scope
- PDF to image conversion (fitz render)
- mimo-v2.6-flash vision endpoint for OCR
- Signature/seal detection
- PDF comparison (visual diff)
- Frontend integration

### Out of Scope
- Handwriting recognition (OCR only)
- Image enhancement/preprocessing

## Acceptance Criteria

1. [ ] Scanned PDFs are OCR'd successfully
2. [ ] Signatures and seals are detected
3. [ ] PDF comparison shows visual differences
4. [ ] Vision uses mimo-v2.6-flash model
5. [ ] Image conversion produces quality output

## Technical Notes

- mimo-v2.6-flash: 1M context, the router's vision default (`src/pdf_modifier/ai/router.py`). It replaced mimo-v2.5, which NaN retired on 2026-09-30
- Use `image_url` content type for vision input
- Convert PDF pages to PNG at 150 DPI for OCR
