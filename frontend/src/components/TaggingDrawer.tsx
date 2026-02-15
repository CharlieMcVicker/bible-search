import { useState } from "react";
import { X, Check, Plus } from "lucide-react";
import clsx from "clsx";
import { motion, AnimatePresence } from "framer-motion";
import { AVAILABLE_TAGS } from "../constants";

interface TaggingDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  word?: string;
  sentenceId?: string;
  wordIndex?: number;
  currentTag?: string | null;
  onTagSelected: (tag: string | null) => void;
}

export default function TaggingDrawer({
  isOpen,
  onClose,
  word,
  sentenceId,
  wordIndex,
  currentTag,
  onTagSelected,
}: TaggingDrawerProps) {
  const [customTag, setCustomTag] = useState("");
  const [loading, setLoading] = useState(false);

  const handleTag = async (tag: string | null) => {
    setLoading(true);
    try {
      const isRemoval = tag === null;
      const response = await fetch(`/api/sentences/${sentenceId}/tags`, {
        method: isRemoval ? "DELETE" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word_index: wordIndex, tag: tag || "" }),
      });
      if (response.ok) {
        onTagSelected(tag);
        onClose();
      }
    } catch (err) {
      console.error("Failed to tag word:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="drawer-overlay open"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="drawer-content"
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="drawer-close" onClick={onClose}>
              <X size={24} />
            </button>

            <div className="mb-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-1">
                Tagging Word
              </h3>
              <p className="text-3xl font-bold text-blue-700">{word}</p>
              {currentTag && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="badge bg-blue-100 text-blue-700">
                    Current: {currentTag}
                  </span>
                  <button
                    onClick={() => handleTag(null)}
                    className="text-xs text-red-500 hover:underline font-bold"
                    disabled={loading}
                  >
                    Remove Tag
                  </button>
                </div>
              )}
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Ref: {sentenceId} (Index: {wordIndex})
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-8">
              {AVAILABLE_TAGS.map((tag) => (
                <motion.button
                  key={tag}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={clsx("tag-option", currentTag === tag && "active")}
                  onClick={() => handleTag(tag)}
                  disabled={loading}
                >
                  {tag}
                </motion.button>
              ))}
            </div>

            <div className="relative">
              <h4 className="text-xs font-bold uppercase text-slate-400 mb-2">
                Custom Tag
              </h4>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input"
                  placeholder="Enter custom tag..."
                  value={customTag}
                  onChange={(e) => setCustomTag(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleTag(customTag)}
                />
                <button
                  className="btn btn-primary px-4"
                  onClick={() => handleTag(customTag)}
                  disabled={loading || !customTag}
                >
                  {loading ? (
                    <Check className="animate-pulse" />
                  ) : (
                    <Plus size={20} />
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
