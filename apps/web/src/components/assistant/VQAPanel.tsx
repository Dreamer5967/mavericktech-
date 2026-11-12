import React, { ChangeEvent, useRef, useState } from 'react';
import { Camera, Upload, X, Loader2, Sparkles } from 'lucide-react';
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
      <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-lg border border-[#45C982]/30 bg-[#45C982]/10">
        <Sparkles className="w-4 h-4 text-[#45C982] flex-shrink-0 mt-0.5" />
        <p className="text-xs text-[#45C982] leading-relaxed font-mono">
          <strong>Google Gemini Visual Question Answering (VQA).</strong> Sends selected camera frame
          and operator question to Gemini. Answers are visual model estimates — not authoritative sensor ground truth.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left column: image source selection */}
        <div className="space-y-3">
          {/* Junction selection */}
          <div>
            <label className="block text-xs font-mono text-white/60 mb-1">
              Camera / Junction feed:
            </label>
            <select
              value={junctionId}
              onChange={(e) => {
                setJunctionId(e.target.value as JunctionId | '');
                setCameraLoadError(false);
              }}
              disabled={isPending}
              className="w-full text-xs font-mono border border-white/15 rounded px-2.5 py-1.5 bg-[#080D10] text-white focus:outline-none focus:border-[#45C982] focus:ring-1 focus:ring-[#45C982] disabled:opacity-50"
            >
              {JUNCTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-[#111A1D] text-white">
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Live Camera Preview */}
          {junctionId && !imagePreview && (
            <div className="relative rounded-lg border border-white/10 bg-[#080D10] h-48 flex items-center justify-center overflow-hidden">
              {!cameraLoadError ? (
                <img
                  src={`/api/v1/frames/${junctionId}`}
                  alt={`Ingress view ${junctionId}`}
                  className="w-full h-full object-cover"
                  onError={() => setCameraLoadError(true)}
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-white/40 text-xs p-4 text-center font-mono">
                  <Camera className="w-6 h-6 mb-2 text-white/20" />
                  <span>No live frame buffer for {junctionId}</span>
                  <span className="text-[10px] text-white/30 mt-1">
                    Frame requested directly from /api/v1/frames/{junctionId}
                  </span>
                </div>
              )}
              <span className="absolute bottom-2 left-2 text-[10px] font-mono bg-[#080D10]/80 text-[#45C982] px-2 py-0.5 rounded border border-white/10">
                CAM_{junctionId}_ROADSIDE
              </span>
            </div>
          )}

          {/* Custom image upload option */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-mono text-white/60">
                Or upload an image file:
              </label>
              {imageFile && (
                <button
                  type="button"
                  onClick={clearCustomImage}
                  className="text-xs font-mono text-red-400 hover:text-red-300 flex items-center gap-1"
                >
                  <X className="w-3 h-3" />
                  Remove
                </button>
              )}
            </div>

            {imagePreview ? (
              <div className="relative rounded-lg border border-white/10 bg-[#080D10] h-48 flex items-center justify-center overflow-hidden">
                <img
                  src={imagePreview}
                  alt="Custom input"
                  className="w-full h-full object-contain"
                />
                <span className="absolute bottom-2 left-2 text-[10px] font-mono bg-[#080D10]/80 text-white/80 px-2 py-0.5 rounded border border-white/10">
                  {imageFile?.name} ({(imageFile!.size / 1024).toFixed(0)} KB)
                </span>
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-white/20 hover:border-[#45C982]/50 bg-[#080D10] rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors"
              >
                <Upload className="w-6 h-6 text-white/40 mb-2" />
                <span className="text-xs font-mono text-white/70">Click to upload a road image</span>
                <span className="text-[10px] font-mono text-white/40 mt-1">JPEG or PNG, up to 10 MB</span>
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              onChange={handleFileChange}
              className="hidden"
            />

            {imageError && (
              <p className="mt-1 text-xs font-mono text-red-400">{imageError}</p>
            )}
          </div>
        </div>

        {/* Right column: question input and presets */}
        <div className="flex flex-col justify-between space-y-3">
          <div>
            <label className="block text-xs font-mono text-white/60 mb-1">
              Visual question:
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isPending}
              rows={4}
              placeholder="e.g. Is the north approach clear? How many cars are visible? Is there an emergency vehicle?"
              className="w-full text-xs font-mono border border-white/15 rounded-lg px-3 py-2 bg-[#080D10] text-white placeholder-white/30 focus:outline-none focus:border-[#45C982] focus:ring-1 focus:ring-[#45C982] resize-none disabled:opacity-50"
            />

            {/* Quick question suggestions */}
            <div className="mt-2 space-y-1">
              <span className="text-[10px] font-mono text-white/40 uppercase tracking-wider block">
                Suggested questions:
              </span>
              {[
                'How many vehicles are visible at this junction?',
                'Is there any vehicle blocking the intersection box?',
                'Are traffic signals or cameras occluded?',
                'Is there an emergency vehicle with flashing lights?',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setQuestion(suggestion)}
                  disabled={isPending}
                  className="block text-left text-xs font-mono text-white/60 hover:text-[#45C982] transition-colors truncate max-w-full cursor-pointer"
                >
                  &rsaquo; {suggestion}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="w-full py-2.5 px-4 rounded-lg bg-[#45C982] hover:bg-[#3db874] text-[#080D10] text-xs font-mono font-bold tracking-wide transition-all shadow-sm shadow-[#45C982]/20 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Submitting to Gemini…</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Analyze Frame with Gemini</span>
                </>
              )}
            </button>
            {!imageB64 && !junctionId && (
              <p className="mt-1 text-[10px] font-mono text-[#E9A23B] text-center">
                Select a junction or upload an image to submit.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
