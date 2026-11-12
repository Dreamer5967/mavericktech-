import React, { ChangeEvent, useRef, useState } from 'react';
import { Camera, AlertTriangle, Upload, X, Loader2, Sparkles } from 'lucide-react';
import { JunctionId } from '../../types/api';

const JUNCTION_OPTIONS: { value: JunctionId | ''; label: string }[] = [
  { value: 'J1', label: 'J1 — North Intersection' },
  { value: 'J2', label: 'J2 — East Intersection' },
  { value: 'J3', label: 'J3 — South Intersection' },
  { value: 'J4', label: 'J4 — West Intersection' },
  { value: '', label: 'Custom uploaded image only' },
];

const MAX_IMAGE_BYTES = 10 * 1024 * 1024; // 10 MB

interface VQAPanelProps {
  onSubmitVQA: (imageB64: string | undefined, question: string, junctionId: JunctionId | null) => void;
  isPending: boolean;
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const b64 = result.split(',')[1];
      if (b64) resolve(b64);
      else reject(new Error('Could not read file'));
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export const VQAPanel: React.FC<VQAPanelProps> = ({ onSubmitVQA, isPending }) => {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [cameraLoadError, setCameraLoadError] = useState(false);
  const [question, setQuestion] = useState('');
  const [junctionId, setJunctionId] = useState<JunctionId | ''>('J1');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageError(null);

    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setImageError('Only JPEG and PNG images are accepted.');
      return;
    }

    if (file.size > MAX_IMAGE_BYTES) {
      setImageError(`Image is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 10 MB.`);
      return;
    }

    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));

    try {
      const b64 = await fileToBase64(file);
      setImageB64(b64);
    } catch {
      setImageError('Could not read the image file.');
    }
  };

  const clearCustomImage = () => {
    setImageFile(null);
    setImageB64(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    setImageError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = () => {
    const q = question.trim();
    if (!q || isPending) return;
    if (!imageB64 && !junctionId) return;

    onSubmitVQA(imageB64 || undefined, q, junctionId || null);
  };

  const canSubmit = (!!imageB64 || !!junctionId) && !!question.trim() && !isPending;

  return (
    <div className="space-y-4">
      {/* Disclaimer warning banner */}
      <div className="flex items-start gap-2 px-3 py-2.5 rounded border border-[#23865A]/30 bg-[#F0FDF4]">
        <Sparkles className="w-4 h-4 text-[#23865A] flex-shrink-0 mt-0.5" />
        <p className="text-xs text-[#23865A] leading-relaxed">
          <strong>Google Gemini Visual Question Answering (VQA).</strong> Sends selected camera frame
          and operator question to Gemini. Answers are visual model estimates — not authoritative sensor ground truth.
        </p>
      </div>

      {/* Junction Selector & Camera Context */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Camera className="w-4 h-4 text-[#737373]" />
          <label className="text-xs font-medium text-[#262626] whitespace-nowrap">Camera source:</label>
          <select
            value={junctionId}
            onChange={(e) => {
              setJunctionId(e.target.value as JunctionId | '');
              setCameraLoadError(false);
            }}
            disabled={isPending}
            className="text-xs border border-[#E5E5E5] rounded px-2.5 py-1.5 bg-white text-[#262626] focus:outline-none focus:ring-1 focus:ring-[#171717] disabled:opacity-50"
          >
            {JUNCTION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {junctionId && (
          <span className="text-[11px] font-mono text-[#737373]">
            Target: cam_{junctionId.toLowerCase()}_roadside
          </span>
        )}
      </div>

      {/* Frame Preview Area */}
      <div>
        <p className="text-xs font-medium text-[#262626] mb-2 flex items-center justify-between">
          <span>Active Camera Frame</span>
          <span className="text-[10px] text-[#737373] font-normal">
            {imagePreview ? 'Using custom uploaded frame' : junctionId ? `Live roadside frame (${junctionId})` : 'No frame selected'}
          </span>
        </p>

        {imagePreview ? (
          /* Custom image uploaded preview */
          <div className="relative inline-block">
            <img
              src={imagePreview}
              alt="Custom uploaded frame"
              className="max-h-48 rounded border border-[#E5E5E5] object-contain bg-[#FAFAFA]"
            />
            <button
              onClick={clearCustomImage}
              disabled={isPending}
              className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-[#C0392B] text-white flex items-center justify-center hover:bg-[#A93226] transition-colors"
              title="Remove custom image"
            >
              <X className="w-3 h-3" />
            </button>
            {imageFile && (
              <p className="mt-1 text-[10px] text-[#737373] font-mono">
                {imageFile.name} · {(imageFile.size / 1024).toFixed(0)} KB (Custom upload)
              </p>
            )}
          </div>
        ) : junctionId ? (
          /* Live Camera API Frame Preview */
          <div className="relative inline-block border border-[#E5E5E5] rounded overflow-hidden bg-[#FAFAFA]">
            {!cameraLoadError ? (
              <img
                src={`/api/v1/frames/${junctionId}?t=${Date.now()}`}
                alt={`Roadside camera frame for ${junctionId}`}
                onError={() => setCameraLoadError(true)}
                className="max-h-48 w-auto object-contain block bg-[#171717]"
              />
            ) : (
              <div className="h-36 w-64 flex flex-col items-center justify-center p-4 text-center bg-[#FFF5F5] border border-[#C0392B]/30 rounded">
                <AlertTriangle className="w-5 h-5 text-[#C0392B] mb-1" />
                <span className="text-xs font-semibold text-[#C0392B]">Camera Frame Unavailable</span>
                <span className="text-[10px] text-[#737373] mt-0.5">
                  Roadside sensor is MISSING or offline.
                </span>
              </div>
            )}
            <div className="absolute bottom-1 right-2 bg-black/70 text-white font-mono text-[9px] px-1.5 py-0.5 rounded">
              AEGIS CAMERA API · {junctionId}
            </div>
          </div>
        ) : (
          /* Fallback dropzone when no junction is selected */
          <label className="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-[#E5E5E5] rounded cursor-pointer bg-[#FAFAFA] hover:bg-[#F5F5F5] transition-colors group">
            <Upload className="w-5 h-5 text-[#A3A3A3] mb-1 group-hover:text-[#737373]" />
            <span className="text-xs text-[#737373]">Click to upload a custom frame</span>
            <span className="text-[10px] text-[#A3A3A3]">JPEG or PNG · max 10 MB</span>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              onChange={handleFileChange}
              disabled={isPending}
              className="hidden"
            />
          </label>
        )}

        {/* Optional upload override toggle if using junction camera */}
        {!imagePreview && junctionId && (
          <div className="mt-2">
            <label className="inline-flex items-center gap-1.5 text-xs text-[#737373] hover:text-[#171717] cursor-pointer">
              <Upload className="w-3.5 h-3.5" />
              <span>Or upload custom frame override</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleFileChange}
                disabled={isPending}
                className="hidden"
              />
            </label>
          </div>
        )}

        {imageError && (
          <p className="mt-1 text-xs text-[#C0392B] flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {imageError}
          </p>
        )}
      </div>

      {/* Question input */}
      <div>
        <p className="text-xs font-medium text-[#262626] mb-1.5">Question for Gemini</p>
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value.slice(0, 500))}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSubmit();
            }}
            disabled={isPending}
            maxLength={500}
            placeholder="e.g. How many vehicles are queued? What color is the signal?"
            className="flex-1 text-sm border border-[#E5E5E5] rounded px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[#171717] disabled:opacity-50 bg-white text-[#262626]"
          />
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="px-3.5 py-2 rounded border border-[#171717] bg-[#171717] text-white text-xs font-medium hover:bg-[#262626] transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5 whitespace-nowrap"
          >
            {isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-[#23865A]" />
            )}
            {isPending ? 'Querying Gemini…' : 'Analyse with Gemini'}
          </button>
        </div>
      </div>
    </div>
  );
};
