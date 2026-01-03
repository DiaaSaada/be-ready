import { useState, useRef } from 'react';

const ALLOWED_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
};

const MAX_FILES = 5;
const MAX_SIZE_MB = 10;

function FileUpload({ onFilesChange, disabled }) {
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    const fileErrors = [];

    // Check type
    const ext = file.name.split('.').pop().toLowerCase();
    const validExts = ['pdf', 'docx', 'txt'];
    if (!validExts.includes(ext)) {
      fileErrors.push(`${file.name}: Invalid file type. Allowed: PDF, DOCX, TXT`);
    }

    // Check size
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      fileErrors.push(`${file.name}: File too large. Maximum ${MAX_SIZE_MB}MB`);
    }

    return fileErrors;
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const newErrors = [];

    // Check total count
    if (files.length + selectedFiles.length > MAX_FILES) {
      newErrors.push(`Maximum ${MAX_FILES} files allowed`);
      setErrors(newErrors);
      return;
    }

    // Validate each file
    const validFiles = [];
    selectedFiles.forEach((file) => {
      const fileErrors = validateFile(file);
      if (fileErrors.length === 0) {
        validFiles.push(file);
      } else {
        newErrors.push(...fileErrors);
      }
    });

    const updatedFiles = [...files, ...validFiles];
    setFiles(updatedFiles);
    setErrors(newErrors);
    onFilesChange(updatedFiles);

    // Reset input
    e.target.value = '';
  };

  const removeFile = (index) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    onFilesChange(updatedFiles);
    setErrors([]);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf':
        return (
          <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8.5 13H10v5H8.5v-5zm2 0h2a1.5 1.5 0 0 1 0 3h-.5v2h-1.5v-5zm2 2h.5v-1h-.5v1zM15 13h2v1h-2v1h1.5v1H15v2h-1.5v-5H17v1z" />
          </svg>
        );
      case 'docx':
        return (
          <svg className="w-8 h-8 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM9.5 14.5l1 3.5 1-3.5h1.5l1 3.5 1-3.5h1.5l-2 5h-1.5l-1-3.5-1 3.5H9.5l-2-5h1.5z" />
          </svg>
        );
      default:
        return (
          <svg className="w-8 h-8 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8 12h8v2H8v-2zm0 4h8v2H8v-2z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${disabled ? 'bg-gray-100 cursor-not-allowed opacity-60' : 'hover:border-blue-500 hover:bg-blue-50'}
          ${files.length > 0 ? 'border-green-300 bg-green-50' : 'border-gray-300'}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-gray-600">
            <span className="font-medium text-blue-600">Click to upload</span> or
            drag and drop
          </p>
          <p className="text-sm text-gray-500">
            PDF, DOCX, or TXT (max {MAX_SIZE_MB}MB each, up to {MAX_FILES} files)
          </p>
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, index) => (
            <li
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div className="flex items-center gap-3">
                {getFileIcon(file.name)}
                <div>
                  <p className="font-medium text-gray-900 truncate max-w-xs">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(index);
                }}
                disabled={disabled}
                className="p-2 text-red-500 hover:bg-red-100 rounded-full transition-colors disabled:opacity-50"
                title="Remove file"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <ul className="text-sm text-red-700 space-y-1">
            {errors.map((error, i) => (
              <li key={i} className="flex items-start gap-2">
                <svg
                  className="w-4 h-4 mt-0.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                {error}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
