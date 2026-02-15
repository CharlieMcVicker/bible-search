import { useState } from "react";
import { Check, Plus } from "lucide-react";
import clsx from "clsx";
import { motion } from "framer-motion";
import { AVAILABLE_TAGS } from "../constants";

interface TaggingOptionsProps {
  word: string;
  sentenceId: string;
  wordIndex: number;
  currentTag?: string | null;
  onTagSelected: (tag: string | null) => void;
}

export default function TaggingOptions({
  word,
  sentenceId,
  wordIndex,
  currentTag,
  onTagSelected,
}: TaggingOptionsProps) {
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
      }
    } catch (err) {
      console.error("Failed to tag word:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 mb-4 pt-4 border-t border-slate-100"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Tagging: <span className="text-blue-600 normal-case">{word}</span>
          </h3>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-40"
            placeholder="Custom tag..."
            value={customTag}
            onChange={(e) => setCustomTag(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleTag(customTag)}
          />
          <button
            className="p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            onClick={() => handleTag(customTag)}
            disabled={loading || !customTag}
          >
            {loading ? (
              <Check size={16} className="animate-pulse" />
            ) : (
              <Plus size={16} />
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        {AVAILABLE_TAGS.map((tag) => (
          <button
            key={tag}
            onClick={() => handleTag(tag)}
            disabled={loading}
            className={clsx(
              "tag-option text-sm",
              currentTag === tag && "active",
            )}
          >
            {tag}
          </button>
        ))}
        {currentTag && (
          <button
            onClick={() => handleTag(null)}
            disabled={loading}
            className="tag-option text-sm text-red-500 hover:text-red-700 hover:border-red-200 hover:bg-red-50"
          >
            Remove Tag
          </button>
        )}
      </div>
    </motion.div>
  );
}
