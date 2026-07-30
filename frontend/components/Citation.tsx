import React from 'react';

interface CitationProps {
  id: string;
  url?: string;
  title?: string;
}

export const Citation: React.FC<CitationProps> = ({ id, url, title }) => {
  return (
    <a
      href={url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center px-1.5 py-0.5 ml-1 text-xs font-semibold text-blue-700 bg-blue-100 rounded hover:bg-blue-200 transition-colors"
      title={title || `Source ${id}`}
    >
      [{id}]
    </a>
  );
};
