export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;
export const ALLOWED_MIME_TYPES = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);

export function isAllowedFileType(file) {
  if (!file) return false;
  return ALLOWED_MIME_TYPES.has(file.type);
}

export function isAllowedFileSize(file) {
  if (!file) return false;
  return file.size <= MAX_FILE_SIZE_BYTES;
}
