import React, { useState } from 'react';
import { Button } from 'components/common/Button';

interface ImageUploadFormProps {
  onSubmit: (image: File) => void;
  loading?: boolean;
}

export const ImageUploadForm: React.FC<ImageUploadFormProps> = ({
  onSubmit,
  loading = false
}) => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedImage) {
      alert('Please select an image first');
      return;
    }
    onSubmit(selectedImage);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: 'var(--spacing-sm)',
          fontWeight: '600',
          color: 'var(--dark)'
        }}>
          Select Medical Image
        </label>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          disabled={loading}
          style={{
            width: '100%',
            padding: 'var(--spacing-sm)',
            border: '2px dashed #e9ecef',
            borderRadius: 'var(--radius-md)',
            cursor: 'pointer'
          }}
        />
      </div>

      {/* Image Preview */}
      {preview && (
        <div style={{ marginBottom: 'var(--spacing-lg)', textAlign: 'center' }}>
          <img
            src={preview}
            alt="Selected medical image"
            style={{
              maxWidth: '300px',
              maxHeight: '300px',
              borderRadius: 'var(--radius-md)',
              border: '2px solid #e9ecef'
            }}
          />
        </div>
      )}

      <Button
        type="submit"
        disabled={loading || !selectedImage}
        loading={loading}
        variant="primary"
        style={{ width: '100%' }}
      >
        📸 Analyze Image
      </Button>
    </form>
  );
};